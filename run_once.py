# run_once.py
# 12/15/08
# This is a setup script that imports all of our twitter logins and otherwise gets things ready to rumble.
# It reads from csv files formatted as "username,password\n" for each account.

from database import *

# Our twitter accounts
print "Adding Twitter Accounts"

f = open("logins.txt", "r")
for line in f.readlines():
  username, password = line.split(",")
  if username and password:
    database.findOrCreateLogin(username, password)
f.close()

# Our realboy accounts
print "Adding Realboy Accounts"

f = open("realboys.txt", "r")
for line in f.readlines():
  username, password = line.split(",")
  if username and password:
    database.findOrCreateRealboy(username, password)
f.close()

# Seed the DB with at least one user
print "Adding Seed User"
database.findOrCreateByUsername("gregmarra")

print "Flushing DB"
database.flush()

print "Done."
