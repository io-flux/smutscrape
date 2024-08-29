# Just a scraper for smut, folks. 🍆💦

A Python-based scraper for downloading adult content from various websites. 😈

## Requirements 🧰
- Python 3.10+ 🐍
- pip 📦
- Optional: conda 🐼

## Installation 🛠️
1. **Clone this repo. 📂**

```bash
git clone https://github.com/io-flux/smutscrape.git
cd smutscrape
```

2. **Install dependencies. 🚀**
 - 🐍 If using conda (recommended) :
```bash
conda create -n smutscrape python=3.10.13 
conda activate smutscrape
pip install -r requirements.txt
```

 - Otherwise:
```bash
pip3 install -r requirements.txt
```

3. **Customize `config.yaml` file to your system/needs. ⚙️**
🛠️ Pay particular attention to these sections:
 - `download_destinations` 💾
 - `ignored` 🚫
 - `vpn` 🤫
   
4. **Make script executable. 🚀**
```bash
chmod +x scrape.py
```

6. Optional: Create a system-wide symlink. 🔗
This allows you to run `scrape` from any directory:
```bash
sudo ln -s $(realpath ./scrape.py) /usr/local/bin/scrape
```
*See note on "Symlink Usage"*

## Usage 🚀
### Basic Usage

```bash
cd smutscrape # if not already in the repo folder
./scrape.py {{ site abbreviation }} {{ mode }} "{{ query }}"
```

### Supported sites & modes 🌐
The following sites and modes are presently supported:
- `9v`: **9vids.com**
  * `search`
- `if`: **incestflix.com**
  * `search`
  * `double_search`
- `lf`: **lonefun.com**
  * `search`
- `ph`: **pornhub.com**
  * `search`
  * `category`
  * `channel`
  * `model`
- `sb`: **spankbang.com**
  * `search`
  * `tag`
  * `model`

**Note:** In addition to the modes specified for each site above, you can always download individual videos using the direct URL by specifying a valid URL from one of the sites with a .yaml.

### Examples 🧐
#### 👧 *To download all videos from 9vids.com's "sister" search results:*

```bash
./scrape.py 9v search sister` 
```

#### 🦉 *To download all videos from the model "owlcrystal" on pornhub.com:*
```bash
./scrape.py ph model "owlcrystal"
```

#### 🛀🧒🏻💦👩🏻 *To download the video "Taboo mom son bath" from SpankBang:*

```bash
./scrape https://spankbang.com/2ei5s/video/taboo+mom+son+bath
```

### Symlink Usage 🔗
Note: if you take the optional step of creating a symlink at `/usr/local/bin/scrape`, you can run the `scrape` (instead of `./scrape.py`) command from any folder and don't need to `cd smutscrape` first: 

```bash
scrape {{ site config abbreviation per the configs folder }} {{ mode }} "{{ query }}"
```

👨‍👩‍👧‍👦 *So now, for example, to download all videos from the "family" tag on spankbang.com:*
```bash
scrape sb tag "family"
```


## Contributions 🤝
Please feel free to help grow the `./configs/` library! 📚

A related need is to add a Selenium mode for sites with trickier javascript (e.g. Motherless) 🕸️

## Troubleshooting 🔧
If you encounter any issues:
1. Check that your `config.yaml` is correctly set up. 📝
2. Ensure you have the latest version of the script and dependencies. 🔄
3. Check the console output for any error messages. 🚨

## Disclaimer ⚠️

No one is responsible for how you use it except you. Please scrape responsibly. 🧠💭

