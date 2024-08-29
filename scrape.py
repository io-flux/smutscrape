#!/usr/bin/env python3

import argparse
import yaml
import requests
from bs4 import BeautifulSoup
import os
import subprocess
import time
import re
import sys
import urllib.parse
from smb.SMBConnection import SMBConnection
import random
from loguru import logger
from tqdm import tqdm
import io
import shlex
import json

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(SCRIPT_DIR, 'configs')

last_vpn_action_time = 0
session = requests.Session()

def load_config(config_file):
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)

def load_site_config(site):
    config_path = os.path.join(CONFIG_DIR, f'{site}.yaml')
    return load_config(config_path)

def process_title(title, invalid_chars):
    for char in invalid_chars:
        title = title.replace(char, "")
    return title

def construct_filename(title, site_config, general_config):
    prefix = site_config.get('name_prefix', '')
    suffix = site_config.get('name_suffix', '')
    processed_title = process_title(title, general_config['file_naming']['invalid_chars'])
    return f"{prefix}{processed_title}{suffix}{general_config['file_naming']['extension']}"

def construct_url(base_url, pattern, site_config, **kwargs):
    encoding_rules = site_config.get('url_encoding_rules', {})

    encoded_kwargs = {}
    for k, v in kwargs.items():
        if isinstance(v, str):
            encoded_v = urllib.parse.quote(v)
            for original, replacement in encoding_rules.items():
                encoded_v = encoded_v.replace(original, replacement)
            encoded_kwargs[k] = encoded_v
        else:
            encoded_kwargs[k] = v

    path = pattern.format(**encoded_kwargs)
    return urllib.parse.urljoin(base_url, path)

def fetch_page(url, user_agents, headers):
    if 'User-Agent' not in headers:
        headers['User-Agent'] = random.choice(user_agents)
    logger.debug(f"Fetching URL: {url}")
    logger.debug(f"Using headers: {headers}")
    time.sleep(random.uniform(1, 3))  # Random delay between requests
    try:
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

def extract_data(soup, selectors):
    data = {}
    for field, config in selectors.items():
        logger.debug(f"Extracting field: {field}")
        logger.debug(f"Config: {config}")
        if isinstance(config, str):
            elements = soup.select(config)
        elif isinstance(config, dict):
            if 'selector' in config:
                elements = soup.select(config['selector'])
            elif 'attribute' in config:
                elements = [soup]
            else:
                elements = []
        logger.debug(f"Found {len(elements)} elements")
        if elements:
            if isinstance(config, dict) and 'attribute' in config:
                value = elements[0].get(config['attribute'])
                if field == 'download_url':
                    logger.debug(f"Download URL element: {elements[0]}")
                    logger.debug(f"Download URL attributes: {elements[0].attrs}")
            else:
                value = elements[0].text.strip()

            if isinstance(config, dict) and 'json_key' in config:
                try:
                    json_data = json.loads(value)
                    value = json_data.get(config['json_key'])
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON for field {field}")

            if field in ['tags', 'genres', 'actors', 'producers']:
                value = [element.text.strip() for element in elements]

            data[field] = value
        logger.debug(f"Extracted data for {field}: {data.get(field)}")
    return data

def process_list_page(url, site_config, general_config, current_page=1, mode=None, identifier=None, overwrite_files=False, headers=None):
    logger.info(f"Processing list page: {url}")
    soup = fetch_page(url, general_config['user_agents'], headers)
    if soup is None:
        logger.error(f"Failed to fetch list page: {url}")
        return None, None

    list_scraper = site_config['scrapers']['list_scraper']
    base_url = site_config['base_url']

    logger.debug(f"Looking for video container with selector: {list_scraper['video_container']['selector']}")
    container = None
    for selector in list_scraper['video_container']['selector']:
        container = soup.select_one(selector)
        if container:
            logger.debug(f"Found container using selector: {selector}")
            break

    if not container:
        logger.error(f"Could not find the video results container. URL: {url}")
        return None, None

    logger.debug(f"Looking for video items with selector: {list_scraper['video_item']['selector']}")
    video_elements = container.select(list_scraper['video_item']['selector'])
    logger.debug(f"Found {len(video_elements)} video elements")

    if len(video_elements) == 0:
        logger.info(f"No video elements found on page {current_page}. Aborting pagination.")
        return None, None

    for video_element in video_elements:
        logger.debug(f"Processing video element: {video_element}")
        video_data = extract_data(video_element, list_scraper['video_item']['fields'])
        logger.debug(f"Extracted video data: {video_data}")

        if 'url' in video_data:
            video_url = video_data['url']
            if not video_url.startswith(('http://', 'https://')):
                video_url = f"http:{video_url}" if video_url.startswith('//') else urllib.parse.urljoin(base_url, video_url)
        elif 'video_key' in video_data:
            video_url = construct_url(base_url, site_config['modes']['video']['url_pattern'], site_config, video_id=video_data['video_key'])
        else:
            logger.warning("Unable to construct video URL. Skipping.")
            continue

        video_title = video_data.get('title', '') or video_element.text.strip()

        logger.info(f"Found video: {video_title} - {video_url}")
        process_video_page(video_url, site_config, general_config, overwrite_files, headers)

    logger.debug("Looking for next page")
    pagination_config = list_scraper.get('pagination', {})
    max_pages = pagination_config.get('max_pages', float('inf'))

    if current_page < max_pages:
        logger.debug(f"Current page: {current_page}")
        logger.debug(f"Pagination config: {pagination_config}")
        logger.debug(f"Mode: {mode}")
        logger.debug(f"Identifier: {identifier}")

        if mode is not None and mode in site_config['modes']:
            logger.debug(f"URL pattern: {site_config['modes'][mode]['url_pattern']}")
            url_pattern = site_config['modes'][mode]['url_pattern'].format(**{mode: identifier})
        else:
            logger.warning(f"Invalid mode: {mode}. Using current URL as pattern.")
            url_pattern = url

        if 'subsequent_pages' in pagination_config:
            next_url = pagination_config['subsequent_pages'].format(
                url_pattern=url_pattern,
                page=current_page + 1,
                search=identifier
            )
        else:
            next_page = soup.select_one(pagination_config.get('next_page', {}).get('selector', ''))
            next_url = next_page.get(pagination_config.get('next_page', {}).get('attribute', '')) if next_page else None

        logger.debug(f"Constructed next URL: {next_url}")

        if next_url:
            logger.debug(f"Found next page URL: {next_url}")
            if not next_url.startswith(('http://', 'https://')):
                next_url = urllib.parse.urljoin(base_url, next_url)
            return next_url, current_page + 1

    logger.debug("No next page found or reached maximum pages")
    return None, None

def should_ignore_video(data, ignored_terms):
    for term in ignored_terms:
        term_lower = term.lower()
        url_encoded_term = term.lower().replace(' ', '-')
        for field, value in data.items():
            if isinstance(value, str):
                if term_lower in value.lower() or url_encoded_term in value.lower():
                    logger.info(f"Ignoring video due to term '{term}' found in {field}")
                    return True
            elif isinstance(value, list):
                for item in value:
                    if term_lower in item.lower() or url_encoded_term in item.lower():
                        logger.info(f"Ignoring video due to term '{term}' found in {field}")
                        return True
    return False

def process_video_page(url, site_config, general_config, overwrite_files=False, headers=None):
    global last_vpn_action_time

    vpn_config = general_config.get('vpn', {})
    if vpn_config.get('enabled', False):
        current_time = time.time()
        if current_time - last_vpn_action_time > vpn_config.get('new_node_time', 300):
            handle_vpn(general_config, 'new_node')

    logger.info(f"Processing video page: {url}")
    soup = fetch_page(url, general_config['user_agents'], headers)
    if soup is None:
        logger.error(f"Failed to fetch video page: {url}")
        return

    data = extract_data(soup, site_config['scrapers']['video_scraper'])

    # Check if the video should be ignored
    if should_ignore_video(data, general_config['ignored']):
        logger.info(f"Ignoring video: {data.get('title', url)}")
        return

    file_name = construct_filename(data['title'], site_config, general_config)

    destination_config = general_config['download_destinations'][0]

    if destination_config['type'] == 'smb':
        smb_destination_path = os.path.join(destination_config['path'], file_name)
        if not overwrite_files and file_exists_on_smb(destination_config, smb_destination_path):
            logger.info(f"File '{file_name}' already exists on SMB share. Skipping download.")
            return
        temp_dir = os.path.join(os.getcwd(), 'temp_downloads')
        os.makedirs(temp_dir, exist_ok=True)
        destination_path = os.path.join(temp_dir, file_name)
    else:
        destination_path = os.path.join(destination_config['path'], file_name)
        if not overwrite_files and os.path.exists(destination_path):
            logger.info(f"File '{file_name}' already exists locally. Skipping download.")
            return

    logger.info(f"Downloading: {file_name}")
    if download_file(data.get('download_url', url), destination_path, site_config, general_config):
        if destination_config['type'] == 'smb':
            upload_to_smb(destination_path, smb_destination_path, destination_config)
            os.remove(destination_path)  # Clean up the local temp file

    time.sleep(general_config['sleep']['between_videos'])

def upload_to_smb(local_path, smb_path, destination_config):
    conn = SMBConnection(destination_config['username'], destination_config['password'], "videoscraper", destination_config['server'])
    if conn.connect(destination_config['server'], 445):
        file_size = os.path.getsize(local_path)
        with open(local_path, 'rb') as file:
            with tqdm(total=file_size, unit='B', unit_scale=True, desc="Uploading to SMB") as pbar:
                bytes_uploaded = 0
                while bytes_uploaded < file_size:
                    chunk = file.read(65536)  # Read in 64KB chunks
                    if not chunk:
                        break
                    conn.storeFile(destination_config['share'], smb_path, io.BytesIO(chunk))
                    bytes_uploaded += len(chunk)
                    pbar.update(len(chunk))
        conn.close()
        logger.info(f"File uploaded to SMB share: {smb_path}")
    else:
        logger.error("Failed to connect to SMB share for upload.")

def download_file(url, destination_path, site_config, general_config):
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

    if url.startswith('//'):
        url = 'http:' + url

    user_agent = random.choice(general_config['user_agents'])
    command = site_config['download']['command'].format(
        destination_path=destination_path,
        url=url,
        user_agent=user_agent
    )

    logger.debug(f"Download URL: {url}")
    logger.debug(f"Executing command: {command}")

    if 'yt-dlp' in command:
        success = download_with_ytdlp(command)
    else:
        success = download_with_curl_wget(command)

    if success:
        logger.info("Download completed successfully.")
        return True
    else:
        logger.error("Download failed.")
        return False

def download_with_ytdlp(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    progress_regex = re.compile(r'\[download\]\s+(\d+\.\d+)% of ~?\s*(\d+\.\d+)(K|M|G)iB')
    total_size = None
    pbar = None

    try:
        for line in process.stdout:
            match = progress_regex.search(line)
            if match:
                percent, size, size_unit = match.groups()
                if total_size is None:
                    total_size = float(size) * {'K': 1024, 'M': 1024**2, 'G': 1024**3}[size_unit]
                    pbar = tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading")
                progress = float(percent) * total_size / 100
                pbar.update(progress - pbar.n)
    except KeyboardInterrupt:
        process.terminate()
        logger.warning("Download interrupted.")
        return False
    finally:
        if pbar:
            pbar.close()

    return process.wait() == 0

def download_with_curl_wget(command):
    if 'curl' in command:
        command = command.replace('curl', 'curl -#')

    try:
        args = shlex.split(command)
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        pbar = tqdm(total=100, unit='%', desc="Downloading", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
        last_percent = 0

        while True:
            output = process.stderr.readline()
            logger.debug(f"Curl output: {output.strip()}")

            if output == '' and process.poll() is not None:
                break
            if output:
                if 'curl' in command:
                    if '#' in output:
                        percent = min(output.count('#'), 100)  # Ensure percent doesn't exceed 100
                        pbar.update(percent - last_percent)
                        last_percent = percent
                elif 'wget' in command:
                    if '%' in output:
                        try:
                            percent = min(int(output.split('%')[0].split()[-1]), 100)
                            pbar.update(percent - last_percent)
                            last_percent = percent
                        except ValueError:
                            pass  # Ignore lines that don't contain a valid percentage

        pbar.update(100 - last_percent)  # Ensure the bar reaches 100%
        pbar.close()
        return process.returncode == 0

    except KeyboardInterrupt:
        process.terminate()
        logger.warning("Download interrupted.")
        return False

def file_exists_on_smb(destination_config, path):
    conn = SMBConnection(destination_config['username'], destination_config['password'], "videoscraper", destination_config['server'])
    if conn.connect(destination_config['server'], 445):
        try:
            conn.getAttributes(destination_config['share'], path)
            return True
        except Exception as e:
            logger.debug(f"Error checking file existence on SMB: {e}")
            return False
        finally:
            conn.close()
    else:
        logger.error("Failed to connect to SMB share.")
        return False

def handle_vpn(general_config, action='start'):
    global last_vpn_action_time
    vpn_config = general_config.get('vpn', {})

    if not vpn_config.get('enabled', False):
        return

    vpn_bin = vpn_config.get('vpn_bin', '')

    if action == 'start':
        cmd = vpn_config.get('start_cmd', '').format(vpn_bin=vpn_bin)
    elif action == 'stop':
        cmd = vpn_config.get('stop_cmd', '').format(vpn_bin=vpn_bin)
    elif action == 'new_node':
        cmd = vpn_config.get('new_node_cmd', '').format(vpn_bin=vpn_bin)
    else:
        logger.error(f"Unknown VPN action: {action}")
        return

    try:
        subprocess.run(cmd, shell=True, check=True)
        last_vpn_action_time = time.time()
        logger.info(f"VPN action '{action}' executed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to execute VPN action '{action}': {e}")

def process_direct_link(url, general_config):
    for site_config_file in os.listdir(CONFIG_DIR):
        if site_config_file.endswith('.yaml'):
            site_config = load_site_config(site_config_file[:-5])  # Remove .yaml extension
            if url.startswith(site_config['base_url']):
                logger.info(f"Detected direct link for site: {site_config_file[:-5]}")
                headers = general_config.get('headers', {}).copy()  # Create a copy of the headers
                headers['User-Agent'] = random.choice(general_config['user_agents'])  # Add a random User-Agent
                process_video_page(url, site_config, general_config, overwrite_files=True, headers=headers)
                return True
    return False

def main():
    parser = argparse.ArgumentParser(description='Video Scraper')
    parser.add_argument('args', nargs='+', help='Site identifier and mode, or direct URL')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--overwrite_files', action='store_true', help='Overwrite existing files')
    args = parser.parse_args()

    log_level = "DEBUG" if args.debug else "INFO"
    logger.remove()
    logger.add(sys.stderr, level=log_level)

    general_config = load_config(os.path.join(SCRIPT_DIR, 'config.yaml'))

    # Check if it's a direct link
    if len(args.args) == 1 and args.args[0].startswith('http'):
        if process_direct_link(args.args[0], general_config):
            return
        else:
            logger.error("Unrecognized URL. Please provide a supported direct link or use the standard command format.")
            sys.exit(1)

    # Standard command format
    if len(args.args) < 3:
        logger.error("Invalid number of arguments. Please provide site, mode, and identifier.")
        sys.exit(1)

    site, mode, identifier = args.args[0], args.args[1], ' '.join(args.args[2:])
    site_config = load_site_config(site)

    # Extract headers from general_config
    headers = general_config.get('headers', {})

    handle_vpn(general_config, 'start')

    if mode not in site_config['modes']:
        logger.error(f"Unsupported mode '{mode}' for site '{site}'")
        sys.exit(1)

    if mode == 'video':
        url = construct_url(site_config['base_url'], site_config['modes'][mode]['url_pattern'], site_config, video_id=identifier)
    else:
        url = construct_url(site_config['base_url'], site_config['modes'][mode]['url_pattern'], site_config, **{mode: identifier})

    try:
        if mode == 'video':
            process_video_page(url, site_config, general_config, args.overwrite_files, headers)
        else:
            current_page = 1
            while url:
                logger.info(f"Processing: {url}")
                next_page, new_page_number = process_list_page(url, site_config, general_config, current_page, mode, identifier, args.overwrite_files, headers)
                if next_page is None:
                    break
                url = next_page
                current_page = new_page_number
                time.sleep(general_config['sleep']['between_pages'])
    except KeyboardInterrupt:
        logger.warning("Script interrupted by user. Exiting gracefully...")

    logger.info("Scraping process completed.")

if __name__ == "__main__":
    main()
