import re
import random
from typing import Optional, Tuple

class PhoneAnonymizer:
    # Fun word lists for generating random usernames
    ADJECTIVES = [
        "Happy", "Bouncy", "Cosmic", "Dancing", "Electric", "Fluffy", "Glowing",
        "Hyper", "Jazzy", "Magical", "Nifty", "Quirky", "Sparkly", "Whimsical",
        "Zesty", "Bubbly", "Cheerful", "Dazzling", "Energetic", "Fantastic"
    ]
    
    NOUNS = [
        "Penguin", "Unicorn", "Dragon", "Phoenix", "Wizard", "Ninja", "Panda",
        "Robot", "Dolphin", "Koala", "Raccoon", "Tiger", "Llama", "Octopus",
        "Platypus", "Narwhal", "Giraffe", "Kangaroo", "Hedgehog", "Chameleon"
    ]

    # Regex pattern for cleaning unicode control characters
    UNICODE_CONTROL_CHARS = re.compile(r'[\u200e\u200f\u202a-\u202f\xa0]+')
    
    # Common international country codes and their lengths
    COUNTRY_CODE_LENGTHS = {
        '1': 1,    # North America
        '20': 2,   # Egypt
        '27': 2,   # South Africa
        '30': 2,   # Greece
        '31': 2,   # Netherlands
        '32': 2,   # Belgium
        '33': 2,   # France
        '34': 2,   # Spain
        '36': 2,   # Hungary
        '39': 2,   # Italy
        '40': 2,   # Romania
        '41': 2,   # Switzerland
        '43': 2,   # Austria
        '44': 2,   # UK
        '45': 2,   # Denmark
        '46': 2,   # Sweden
        '47': 2,   # Norway
        '48': 2,   # Poland
        '49': 2,   # Germany
        '51': 2,   # Peru
        '52': 2,   # Mexico
        '53': 2,   # Cuba
        '54': 2,   # Argentina
        '55': 2,   # Brazil
        '56': 2,   # Chile
        '57': 2,   # Colombia
        '58': 2,   # Venezuela
        '60': 2,   # Malaysia
        '61': 2,   # Australia
        '62': 2,   # Indonesia
        '63': 2,   # Philippines
        '64': 2,   # New Zealand
        '65': 2,   # Singapore
        '66': 2,   # Thailand
        '81': 2,   # Japan
        '82': 2,   # South Korea
        '84': 2,   # Vietnam
        '86': 2,   # China
        '90': 2,   # Turkey
        '91': 2,   # India
        '92': 2,   # Pakistan
        '93': 2,   # Afghanistan
        '94': 2,   # Sri Lanka
        '95': 2,   # Myanmar
        '98': 2,   # Iran
        '212': 3,  # Morocco
        '213': 3,  # Algeria
        '216': 3,  # Tunisia
        '218': 3,  # Libya
        '220': 3,  # Gambia
        '221': 3,  # Senegal
        '222': 3,  # Mauritania
        '223': 3,  # Mali
        '234': 3,  # Nigeria
        '249': 3,  # Sudan
        '250': 3,  # Rwanda
        '251': 3,  # Ethiopia
        '252': 3,  # Somalia
        '253': 3,  # Djibouti
        '254': 3,  # Kenya
        '255': 3,  # Tanzania
        '256': 3,  # Uganda
        '257': 3,  # Burundi
        '258': 3,  # Mozambique
        '260': 3,  # Zambia
        '261': 3,  # Madagascar
        '263': 3,  # Zimbabwe
        '264': 3,  # Namibia
        '265': 3,  # Malawi
        '266': 3,  # Lesotho
        '267': 3,  # Botswana
        '268': 3,  # Swaziland
        '269': 3,  # Comoros
        '297': 3,  # Aruba
        '298': 3,  # Faroe Islands
        '299': 3,  # Greenland
        '350': 3,  # Gibraltar
        '351': 3,  # Portugal
        '352': 3,  # Luxembourg
        '353': 3,  # Ireland
        '354': 3,  # Iceland
        '355': 3,  # Albania
        '356': 3,  # Malta
        '357': 3,  # Cyprus
        '358': 3,  # Finland
        '359': 3,  # Bulgaria
        '370': 3,  # Lithuania
        '371': 3,  # Latvia
        '372': 3,  # Estonia
        '373': 3,  # Moldova
        '374': 3,  # Armenia
        '375': 3,  # Belarus
        '376': 3,  # Andorra
        '377': 3,  # Monaco
        '378': 3,  # San Marino
        '380': 3,  # Ukraine
        '381': 3,  # Serbia
        '382': 3,  # Montenegro
        '385': 3,  # Croatia
        '386': 3,  # Slovenia
        '387': 3,  # Bosnia and Herzegovina
        '389': 3,  # Macedonia
        '420': 3,  # Czech Republic
        '421': 3,  # Slovakia
        '423': 3,  # Liechtenstein
        '500': 3,  # Falkland Islands
        '501': 3,  # Belize
        '502': 3,  # Guatemala
        '503': 3,  # El Salvador
        '504': 3,  # Honduras
        '505': 3,  # Nicaragua
        '506': 3,  # Costa Rica
        '507': 3,  # Panama
        '509': 3,  # Haiti
        '590': 3,  # Guadeloupe
        '591': 3,  # Bolivia
        '592': 3,  # Guyana
        '593': 3,  # Ecuador
        '594': 3,  # French Guiana
        '595': 3,  # Paraguay
        '596': 3,  # Martinique
        '597': 3,  # Suriname
        '598': 3,  # Uruguay
        '599': 3,  # Netherlands Antilles
        '670': 3,  # East Timor
        '672': 3,  # Norfolk Island
        '673': 3,  # Brunei
        '674': 3,  # Nauru
        '675': 3,  # Papua New Guinea
        '676': 3,  # Tonga
        '677': 3,  # Solomon Islands
        '678': 3,  # Vanuatu
        '679': 3,  # Fiji
        '680': 3,  # Palau
        '681': 3,  # Wallis and Futuna
        '682': 3,  # Cook Islands
        '683': 3,  # Niue
        '685': 3,  # Samoa
        '686': 3,  # Kiribati
        '687': 3,  # New Caledonia
        '688': 3,  # Tuvalu
        '689': 3,  # French Polynesia
        '690': 3,  # Tokelau
        '691': 3,  # Micronesia
        '692': 3,  # Marshall Islands
        '850': 3,  # North Korea
        '852': 3,  # Hong Kong
        '853': 3,  # Macau
        '855': 3,  # Cambodia
        '856': 3,  # Laos
        '880': 3,  # Bangladesh
        '886': 3,  # Taiwan
        '960': 3,  # Maldives
        '961': 3,  # Lebanon
        '962': 3,  # Jordan
        '963': 3,  # Syria
        '964': 3,  # Iraq
        '965': 3,  # Kuwait
        '966': 3,  # Saudi Arabia
        '967': 3,  # Yemen
        '968': 3,  # Oman
        '970': 3,  # Palestinian Territory
        '971': 3,  # United Arab Emirates
        '972': 3,  # Israel
        '973': 3,  # Bahrain
        '974': 3,  # Qatar
        '975': 3,  # Bhutan
        '976': 3,  # Mongolia
        '977': 3,  # Nepal
        '992': 3,  # Tajikistan
        '993': 3,  # Turkmenistan
        '994': 3,  # Azerbaijan
        '995': 3,  # Georgia
        '996': 3,  # Kyrgyzstan
        '998': 3,  # Uzbekistan
    }

    @staticmethod
    def _generate_fun_username() -> str:
        """Generate a random fun username from adjective + noun combination."""
        adjective = random.choice(PhoneAnonymizer.ADJECTIVES)
        noun = random.choice(PhoneAnonymizer.NOUNS)
        return f"{adjective}{noun}"

    @staticmethod
    def _clean_phone(phone: str) -> str:
        """Clean phone number by removing unicode control characters and normalizing spaces."""
        # Remove unicode control characters and normalize spaces
        cleaned = PhoneAnonymizer.UNICODE_CONTROL_CHARS.sub('', phone)
        # Replace various types of hyphens/dashes with standard hyphen
        cleaned = re.sub(r'[‑–—]', '-', cleaned)
        # Remove any remaining non-digit characters except plus
        cleaned = ''.join(c for c in cleaned if c.isdigit() or c == '+')
        return cleaned

    @staticmethod
    def _extract_country_code(phone: str) -> Tuple[str, str]:
        """
        Extract country code and remaining digits from phone number.
        Uses a comprehensive list of international country codes.
        """
        if not phone.startswith('+'):
            if len(phone) == 10:  # Standard North American number
                return '+1', phone
            return '', phone
            
        # Remove the plus sign for checking
        digits = phone[1:]
        
        # Try matching country codes from longest to shortest
        for length in [3, 2, 1]:
            if len(digits) >= length:
                potential_code = digits[:length]
                if potential_code in PhoneAnonymizer.COUNTRY_CODE_LENGTHS and \
                   PhoneAnonymizer.COUNTRY_CODE_LENGTHS[potential_code] == length:
                    return f'+{potential_code}', digits[length:]
        
        # If no known country code is found, assume first digit is country code
        return f'+{digits[0]}', digits[1:]

    @staticmethod
    def anonymize(phone: str, username: Optional[str] = None) -> Tuple[str, str]:
        """
        Anonymize a phone number and return both the anonymized number and display name.
        
        Args:
            phone: The phone number to anonymize. Can be in any format:
                  - International with country code (e.g., +1234567890)
                  - North American format (e.g., (123) 456-7890)
                  - Local format (e.g., 123-4567)
                  - Any other format with digits and common separators
            username: Optional real username associated with the number
            
        Returns:
            Tuple of (anonymized_phone, display_name)
            The display_name will be prefixed with [👤] for real usernames
            or [🎭] for generated usernames
        """
        # Clean and format the phone number
        cleaned_phone = PhoneAnonymizer._clean_phone(phone)
        
        if len(cleaned_phone) <= 5:  # Handle short numbers
            # For short numbers, keep only the last digit
            last_digit = cleaned_phone[-1]
            stars = '*' * (len(cleaned_phone) - 1)
            anonymized = f"{stars}{last_digit}"
        else:
            # Extract country code and remaining digits
            country_code, remaining = PhoneAnonymizer._extract_country_code(cleaned_phone)
            
            # Keep last 4 digits
            last_four = remaining[-4:] if len(remaining) >= 4 else remaining[-1:]
            # Fill middle with stars
            stars = '*' * 4  # Always use 4 stars for consistency
            
            anonymized = f"{country_code}{stars}{last_four}"

        # Generate display name
        if username:
            # Clean the username of any control characters
            clean_username = PhoneAnonymizer.UNICODE_CONTROL_CHARS.sub('', username)
            display_name = f"[👤] {clean_username}"  # Real username
        else:
            random_name = PhoneAnonymizer._generate_fun_username()
            display_name = f"[🎭] {random_name}"  # Generated username

        return anonymized, display_name

# Example usage
if __name__ == "__main__":
    # Test with various phone numbers and usernames
    test_cases = [
        ("+1 (587) 998‑1598", None),
        ("+44 7464 758875", "John"),
        ("+91 80885 89616", "Alice"),
        ("+234 811 635 8644", None),
        ("‪+1 (443) 739‑6663‬", "Bob"),
        # Additional international formats
        ("+86 123 4567 8901", None),    # China
        ("+971 50 123 4567", None),     # UAE
        ("+81 90 1234 5678", None),     # Japan
        ("+7 916 123 45 67", None),     # Russia
        ("+972 50 123 4567", None),     # Israel
    ]
    
    for phone, name in test_cases:
        anon_phone, display = PhoneAnonymizer.anonymize(phone, name)
        print(f"Original: {phone}")
        print(f"Anonymized: {anon_phone}")
        print(f"Display: {display}")
        print("-" * 40)