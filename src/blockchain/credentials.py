from os.path import expanduser, join, exists
from typing import Optional
import configparser

from src.blockchain.keys import PrivateKey, PublicKey
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

gth_config_folder = expanduser("~/.gth")
credentials_file_name = 'credentials'

# get credentials_file_path if exists
credentials_file_path: Optional[str] = join(
    gth_config_folder,
    credentials_file_name
) if exists(join(gth_config_folder, credentials_file_name)) else None
logger.debug(f"{credentials_file_name} file path: {credentials_file_path}")

private_key_from_config: Optional[PrivateKey] = None
public_key_from_config: Optional[PublicKey] = None

if credentials_file_path is not None:
    credentials_file = configparser.RawConfigParser()
    logger.debug(f'{credentials_file.read(credentials_file_path)=}')
    logger.debug(f'{credentials_file.sections()=}')

    try:
        # Load keys from credentials file
        private_key_from_config = PrivateKey(credentials_file.get('default', 'private_key'))
        public_key_from_config = PublicKey(credentials_file.get('default', 'public_key'))
    except Exception as e:
        logger.warning(f'Could not read credentials from {credentials_file_path} file. {e}')
        private_key_from_config = None
        public_key_from_config = None

# Generate keys if not found in credentials file
PRIVATE_KEY: PrivateKey = private_key_from_config or PrivateKey.generate()
PUBLIC_KEY: PublicKey = public_key_from_config or PublicKey.generate_from_private_key(PRIVATE_KEY)
logger.info(f"Encoded Public Key: {PUBLIC_KEY.encode()}")

