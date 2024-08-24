Just a scraper for smut, folks. 🍆

No one is responsible for how you use it except you. Please scrape responsibly.

## Installation:
1. `git clone git@github.com:io-flux/smut-scrape.git`
2. `cd smut-scrape`
3. If you're using conda or virtual environment: `pip install -r requirements.txt`
   Otherwise: `pip3 install -r requirements.txt`
4. Customize your config.yaml file to your specifications.

## Usage:
`./scrape {{ site config abbreviation per the configs folder }} search "{{ query }}"`

For example, to search for "sister" on 9vids, `./scrape 9v search "sister"`.

Some sites have other list modes besides `search`. For example, `ph` supports `model`, for which correct usage would be `./scrape ph model "renee rose"`

## Contributions

Please feel free to help grow the `./configs/` library!

A related need is to add a Selenium mode for sites with trickier javascript.
