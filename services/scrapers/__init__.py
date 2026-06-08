from .tecnoempleo import TecnoempleoScraper
from .infojobs import InfojobsScraper
from .indeed import IndeedScraper
from .linkedin import LinkedInScraper

SCRAPERS = {
    "tecnoempleo": TecnoempleoScraper,
    "infojobs": InfojobsScraper,
    "indeed": IndeedScraper,
    "linkedin": LinkedInScraper,
}
