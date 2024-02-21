"""
   Copyright (c) Philippe Romano, 2021, 2022
"""

class authentication:

    def __init__(self):
        self.AdminNumbers = [
            '+33632321425'
        ]
        self.AuthorizedNumbers = [
            {'Name': 'Philippe',    'Number': '+33632321425'},
            {'Name': 'Marie', 'Number': '+33620779630'}
        ]

    def __del__(self):
        pass

    def isAuthorized(self, number):
        for n in self.AuthorizedNumbers:
            if number in n['Number']:
                return True
        return False
