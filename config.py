import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'postgres://vwdvuoczqxhjtc:2ae32d34b68e169a426bc46836e732986fcfbafd1fe7741541b503f13f14f702@ec2-34-225-162-157.compute-1.amazonaws.com:5432/d3e0q6d7pajbd5'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SECRET_KEY = 'ThisIsAwildGameOfSurvival'
SQLALCHEMY_TRACK_MODIFICATIONS = False
