#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

import getpass
import gnupg
import os
import sys

from gnupg import _logger
from pprint import pprint

# Ensure log file path exists
log_path = os.path.join(os.path.join(os.getcwd(), 'gnupg'), 'test')
if not os.path.exists(log_path):
    os.makedirs(log_path)

# Set up logging
log = _logger.create_logger(0)
# Levels:
# 0    NOTSET   Disable all logging.
# 9    GNUPG    Log GnuPG's internal status messages.
# 10   DEBUG    Log module level debuging messages.
# 20   INFO     Normal user-level messages.
# 30   WARN     Warning messages.
# 40   ERROR    Error messages and tracebacks.
# 50   CRITICAL Unhandled exceptions and tracebacks.
log.setLevel(0)

NEWKEY_DIR = './gnupg-key'
# NAME = 'Someone'
NAME_COMMENT = None
# NAME_EMAIL = 'someone@example.com'
EXPIRE_DATE = None
# PASSPHRASE = None
KEY_TYPE = 'RSA'
KEY_USAGE = 'cert'
KEY_LENGTH = 4096
SUBKEY_TYPE = 'RSA'
SUBKEY_USAGE = 'sign'
SUBKEY_LENGTH = 4096
KEYSERVER = None
PREFERENCES = None

KEY_FILE_MINE = 'keys_mine_pub_priv.asc'
KEY_FILE_THEIR = 'keys_their_pub.asc'

home = os.path.expanduser('~')
if sys.platform in ["linux", "linux2"]:
    gpg_path = os.path.join(home, '.gnupg')
    _keyring = None
    _secring = None
    _binary = None
elif sys.platform == "win32":
    gpg_path = '{}'.format(os.path.join(home, 'AppData/Roaming/gnupg').replace('\\', '/'))
    _keyring = '{}{}'.format(gpg_path, '/pubring.gpg')
    _secring = '{}{}'.format(gpg_path, '/secring.gpg')
    current_path = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/')
    _binary = '{}/GnuPG/pub/gpg2.exe'.format(current_path)
    print("_binary: {}".format(_binary))


class TooMuchPrivacy:
    """
    Too Much Privacy
    A class for encrypting and decrypting communication
    """

    def __init__(self):
        self.gpg = gnupg.GPG(homedir=gpg_path,
                             binary='gpg2')
        self.gpg.encoding = 'utf-8'
        self.public_keys = self.gpg.list_keys()
        self.private_keys = self.gpg.list_keys(True)
        self.key_priv_id = None
        self.key_pub_id = None
        self.passphrase = None

    def select_keys_and_passphrase(self):
        print("Welcome to Too Much Privacy. Let's get started with selecting what keys to use.")
        print("\nPrivate Keys:")
        key_list_priv = {}
        for index, each_priv_key in enumerate(self.private_keys):
            print("{index}: {key} {uid}".format(index=index+1,
                                                key=each_priv_key['keyid'],
                                                uid=each_priv_key['uids'][0]))
            key_list_priv[str(index+1)] = each_priv_key

        key_priv_not_selected = True
        while key_priv_not_selected:
            selected_priv_key = raw_input("\nSelect the number of the private key to use: ")
            if str(selected_priv_key) in key_list_priv:
                key_priv_not_selected = False
            else:
                print("Invalid choice. Try again.")
        self.key_priv_id = key_list_priv[selected_priv_key]['keyid']

        verify_passphrase = True
        while verify_passphrase:
            self.passphrase = getpass.getpass("\nEnter passphrase for your private key, to decrypt messages: ")
            self.key_pub_id = self.key_priv_id
            str_encrypted = self.encrypt_string("Success")
            str_decrypted = self.decrypt_string(str_encrypted)
            if str(str_decrypted) == 'Success':
                verify_passphrase = False
            else:
                print("Passphrase incorrect. Try again.")

        print("\nPublic Keys:")
        key_list_pub = {}
        for index, each_pub_key in enumerate(self.public_keys):
            print("{index}: {key} {uid}".format(index=index+1,
                                                key=each_pub_key['keyid'],
                                                uid=each_pub_key['uids'][0]))
            key_list_pub[str(index + 1)] = each_pub_key

        key_pub_not_selected = True
        while key_pub_not_selected:
            selected_pub_key = raw_input("\nSelect the number of the public key to use: ")
            if str(selected_pub_key) in key_list_pub:
                key_pub_not_selected = False
            else:
                print("Invalid choice. Try again.")
        self.key_pub_id = key_list_pub[selected_pub_key]['keyid']

        return key_list_priv[selected_priv_key]['uids'][0]

    def create_keys(self):
        """Create public and private PGP keys"""
        try:
            os.system('rm -rf TMP-bit-key')

            # Prompt user for name and email
            name = raw_input("Name:")
            email = raw_input("Email:")

            # Continuously ask for repeated passphrases until passphrases match
            phrases_do_not_match = True
            while phrases_do_not_match:
                self.passphrase = getpass.getpass("Passphrase:")
                passphrase_re = getpass.getpass("Reenter Passphrase:")
                if self.passphrase != passphrase_re:
                    print("Passphrases don't match. Try again.")
                else:
                    phrases_do_not_match = False

            # Dictionary of all gnupg parameters
            allparams = {'name_real': name,
                         'name_comment': NAME_COMMENT,
                         'name_email': email,
                         'expire_date': EXPIRE_DATE,
                         'passphrase': self.passphrase,
                         'key_type': KEY_TYPE,
                         'key_usage': KEY_USAGE,
                         'key_length': KEY_LENGTH,
                         'subkey_type': SUBKEY_TYPE,
                         'subkey_usage': SUBKEY_USAGE,
                         'subkey_length': SUBKEY_LENGTH,
                         'keyserver': KEYSERVER,
                         'preferences': PREFERENCES}

            # Create the batch file
            batchfile = self.create_batch_file(allparams)

            # Create the key
            key, fingerprint = self.create_key(batchfile)

            # Export private and public key
            self.export_keys(key)

            # Import keys
            self.import_keys()

            # List Keys
            public_keys = self.gpg.list_keys()
            private_keys = self.gpg.list_keys(True)
            log.info('public keys:\n')
            pprint(public_keys)
            log.info('private keys:\n')
            pprint(private_keys)

            return True

        except Exception as except_msg:
            log.error("Error while generating key: {err}".format(err=except_msg))
            return False

    def create_batch_file(self, keyparams):
        """
        Create the batchfile for a new PGP key.
        :params dict keyparams: A dictionary of arguments for creating the key.
        :rtype: str
        :returns: A string containing the entire GnuPG batchfile.
        """
        useparams = {}
        for key, value in keyparams.items():
            if value:
                useparams.update({key: value})

        # Generate batchfile from gnupg parameters
        batchfile = self.gpg.gen_key_input(save_batchfile=True,
                                           **useparams)
        log.info("Generated GnuPG batch file:\n {batch}".format(batch=batchfile))
        return batchfile

    def create_key(self, batchfile):
        """Create PGP keys"""
        log.info("Generating key (this may take a while)...")
        key = self.gpg.gen_key(batchfile)
        fingerprint = key.fingerprint

        # Check if fingerprint exists
        if not fingerprint:
            log.error("Key creation seems to have failed: "
                      "{key_stat}".format(key_stat=key.status))
            return None, None

        return key, fingerprint

    def decrypt_string(self, str_encrypted):
        """Decrypt an encrypted string"""
        decrypted_data = self.gpg.decrypt(str_encrypted,
                                          passphrase=self.passphrase)
        if str(decrypted_data) != '':
            return decrypted_data
        else:
            return "###Passphrase unable to decrypt data###"

    def encrypt_string(self, str_unencrypted):
        """Encrypt every character entered using PGP"""
        encrypted_data = self.gpg.encrypt(str_unencrypted, self.key_pub_id)
        str_encrypted = str(encrypted_data)
        # print('\nok: {ok}'.format(ok=encrypted_data.ok))
        # print('\nstatus: {stat}'.format(stat=encrypted_data.status))
        # print('\nstderr: {err}'.format(err=encrypted_data.stderr))
        log.info('Original string:\n{ue_str}'.format(ue_str=str_unencrypted))
        log.info('Encrypted string:\n{e_str}'.format(e_str=str_encrypted))

        return str_encrypted

    def export_keys(self, key):
        """Export PGP keys"""
        ascii_armored_public_keys = self.gpg.export_keys(key)  # same as gpg.export_keys(key, False)
        ascii_armored_private_keys = self.gpg.export_keys(key, True)  # True => private keys
        with open(KEY_FILE_MINE, 'w') as f:
            f.write(ascii_armored_public_keys)
            f.write(ascii_armored_private_keys)
        log.info("Key successfully exported as {key_filename}".format(key_filename=KEY_FILE_MINE))

    def import_keys(self):
        key_data = open(KEY_FILE_MINE).read()
        import_result = self.gpg.import_keys(key_data)
        log.info("Key import results:\n{results}".format(
            results=import_result.results))

    @staticmethod
    def is_ascii(letter):
        """Check if ascii"""
        try:
            letter.decode('ascii')
        except UnicodeDecodeError:
            return False
        return True


if __name__ == "__main__":
    tmp = TooMuchPrivacy()

    try:
        while True:
            print("\nEnter text to encrypt, then press "
                  "Enter:\n")
            str_unencrypted = raw_input()
            str_encrypted = tmp.encrypt_string(str_unencrypted)
            print("Encrypted string'{}'".format(str_encrypted))
            str_decrypted = tmp.decrypt_string(str_encrypted)
            print("Decrypted string:\n{}".format(str_decrypted))
            log.info("Decrypted string:\n{str_decrypt}".format(
                str_decrypt=str_decrypted))
    except KeyboardInterrupt:
        log.info("Keyboard Interrupt: Closing program.")
        sys.exit()
