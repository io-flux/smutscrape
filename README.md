# Just a scraper for smut, folks. 🍆

## Installation:
1. `git clone https://github.com/io-flux/smutscrape.git`
2. `cd smutscrape`
3. If you're using conda or virtual environment:
      `pip install -r requirements.txt`
   Otherwise:
      `pip3 install -r requirements.txt`
5. Customize `config.yaml` file to your specifications.
6. `chmod +x scrape.py`
7. Optional: `sudo ln -s $(realpath ./scrape.py) /usr/local/bin/scrape` to "install" scrape.py as system-wide script (see "Usage Note" below).†

## Usage
From the `smutscrape` folder† (where `scrape.py`, `config.yaml`, and `configs` are saved): 
```
./scrape.py {{ site config abbreviation per the configs folder }} search "{{ query }}"
```

So, for example:
- `./scrape.py 9v search sister` downloads all videos from 9vids.com's "sister" search results.
- `./scrape.py ph model "owlcrystal"` downloads all videos from the model "owlcrystal" on pornhub.com.

† Usage Note: if you take the optional step of creating a symlink at `/usr/local/bin/scrape`, you can run the `scrape` (instead of `./scrape.py`) command from any folder and don't need to `cd smutscrape` first: 
```
scrape {{ site config abbreviation per the configs folder }} search "{{ query }}"
```
Now, for example:
- `scrape sb tag "family"` downloads all videos from the "family" tag on spankbang.com.

## Supported sites & modes:
Some sites have other list modes besides `search`. The following sites and modes are presently supported:
- 9vids.com - `9v`
  * `search`
- incestflix.com - `if`
  * `search`
  * `double_search`
- lonefun.com - `lf`
  * `search`
- pornhub.com - `ph`
  * `search`
  * `category`
  * `channel`
  * `model`
- spankbang.com - `sb`
  * `search`
  * `tag`
  * `model`
 
In addition to the modes specified for each site, you can always download individual videos using the direct URL, e.g.:

```
./scrape https://spankbang.com/5y2rd/video/chloe+night+shower+with+brother
```

## Contributions

Please feel free to help grow the `./configs/` library!

A related need is to add a Selenium mode for sites with trickier javascript (e.g. Motherless)

## Disclaimer

No one is responsible for how you use it except you. Please scrape responsibly.

