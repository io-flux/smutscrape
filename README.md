Just a scraper for smut, folks. 🍆

No one is responsible for how you use it except you. Please scrape responsibly.

## Installation:
1. `git clone git@github.com:io-flux/smutscrape.git`
2. `cd smutscrape`
3. If you're using conda or virtual environment:
      `pip install -r requirements.txt`
   Otherwise:
      `pip3 install -r requirements.txt`
5. Customize `config.yaml` file to your specifications.
6. `chmod +x scrape.py`

## Usage:
`./scrape.py {{ site config abbreviation per the configs folder }} search "{{ query }}"`

For example, to search for "sister" on 9vids, `./scrape.py 9v search "sister"`.

Some sites have other list modes besides `search`. For example, `ph` supports `model`, for which correct usage would be `./scrape.py ph model "renee rose"`

## Contributions

Please feel free to help grow the `./configs/` library!

A related need is to add a Selenium mode for sites with trickier javascript.
