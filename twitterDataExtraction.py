import os
import sys
import csv
import tweepy
import time
import datetime

"""
Python 3 Application utilizing Tweepy.
Fetches a specific tweet from a user, and creates a list of the 
users who follow each other from the comment list of that tweet 
(including the original poster of the tweet).

To run this application:
Use Python 3 with the Tweepy library installed. Insert your personal 
consumer key and consumer secret into the appropriate global variables to
fetch the data.
Run from a terminal as "python twitterDataExtraction.py"



Reference links used to build this application:
-https://stackoverflow.com/questions/52307443/how-to-get-the-replies-for-a-given-tweet-with-tweepy-and-python
-https://stackoverflow.com/questions/25944037/full-list-of-twitter-friends-using-python-and-tweepy
-https://stackoverflow.com/questions/26792734/get-all-friends-of-a-given-user-on-twitter-with-tweepy
-https://stackoverflow.com/questions/17431807/get-all-follower-ids-in-twitter-by-tweepy/17490816#17490816 

"""

# Insert your personal consumer key and secret in these variables.
consumer_key = ""
consumer_secret = ""

# Authorization for using Twitter API.
auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

# Variable that will save all relationships between users.
# First name in list follows the second username in the list. 
relationshipList = []

# Information of the tweet, which is provided in the main function.
aTweetID = -1
aUsername =""

def getCertainTweetAndComments(aTweetID, aUsername):
    """From a specific tweet of a user, fetch the commenters in that tweet."""

    print("ID used: " + str(aTweetID))
    aTweet = api.get_status(aTweetID)
    print("This is the id from the Twitter API: " + aTweet.id_str)
    aListCommenters = []
    # A set data structure is used here so as to avoid saving duplicate users, as 
    # elements in a set are all unique.
    aSetCommenters = set()

    # Gets all replies (up to a 1000) for a specific tweet.
    allReplies = tweepy.Cursor(api.search, q='to:{} filter:replies'.format(aUsername), result_type='recent',since_id=aTweetID,tweet_mode='extended').items(1000)

    # Go through all replies until empty.
    while True:
        try:
            # Get next reply.
            tweet = allReplies.next()
            # If this tweet is not part of a reply/comment, or its attribute of reply is empty, then skip.
            if ((not hasattr(tweet, 'in_reply_to_status_id_str')) or (tweet.in_reply_to_status_id_str=="None")):
                continue
            # If it is a reply...
            if hasattr(tweet,'in_reply_to_status_id_str'):
                print("Comment id:-" + str(tweet.in_reply_to_status_id_str)+"-")
                
                # If the reply is to the tweet we are working on...
                if (tweet.in_reply_to_status_id_str==aTweet.id_str):
                    print("A comment found")
                    # Get commenters username/twitter handle.
                    aScreenName = tweet.user.screen_name
                    print("A commmenter: " + str(aScreenName))
                    # Add new commenter to set.
                    aSetCommenters.add(aScreenName)

        except tweepy.RateLimitError as e:
            print("Twitter api rate limit reached".format(e))
            time.sleep(60)
            continue

        except tweepy.TweepError as e:
            print("Tweepy error occured:{}".format(e))
            break

        except StopIteration:
            break

        except Exception as e:
            print("Failed while fetching replies {}".format(e))
            break
    
    # Convert set to a list.
    aListCommenters = list(aSetCommenters)
    # Print commenters found for this tweet.
    print("List of Commenters: ")
    for x in range(len(aListCommenters)):
        print(str(x) + ". " + str(aListCommenters[x]))
    
    # Return the commenters.
    return aListCommenters

def getFriendsOfUser(aUsername, commenterList):
    """Get the friends of a certain user (who they follow), and compare to the list of commenters in the tweet."""

    aSetFriends = set()
    try:
        # Get user.
        aUser = api.get_user(str(aUsername))
    except:
        # If an error happens, write error to file.
        f = open("errorFile.txt",'a')
        f.write("Error in fetching user -" + str(aUsername) +"-.")
        f.close()
        return
    
    print("Getting friends from : " + str(aUser.screen_name))
    #Counter is used to know progress of getting friends, and how much time has passed in searching.
    aCounter = 0
    tempList = []

    # Get a page of results of friends of a certain user.
    for page in tweepy.Cursor(api.friends, screen_name=aUser.screen_name).pages():
        # Save page.
        tempList.extend(page)
        # Sleep for 60 seconds, according to Twitter API.
        print("Sleeping " + str(aCounter))
        time.sleep(60)
        print("Awake " + str(aCounter))
        aCounter+=1
    
    # Print friends of user found, and add the names to the set.
    for x in tempList:
        print("A Friend found:  " + str(x.screen_name))
        aSetFriends.add(str(x.screen_name))
    
    # Create file with name of user to save the friends inside.
    aFileName = str(aUsername) + ".txt"
    aFile = open(aFileName, 'w')
    for x in tempList:
        aFile.write(str(x.screen_name) + "\n")
    aFile.close()
    
    print(str(len(aSetFriends)) + " friends found.")
    print("Checking for relationships...")
    
    # Add to list of relationships if one of the commenters is in the friends list of the user. 
    for x in range(len(commenterList)):
        if commenterList[x] in aSetFriends:
            relationshipList.append([aUsername,commenterList[x]])
    print("Checking done.")
    printRelationships()

def getAllRelationships(aUsername, commenterList):
    """Get all friends (who that user follows) of users in the tweet."""
    
    # First, get friends of the poster of the tweet.
    getFriendsOfUser(str(aUsername),commenterList)
    # Save the original poster as another user to compare.
    commenterList.append(str(aUsername))

    # Go through all the users, checking if they follow each other (except for the last one,
    # which is the original poster of the tweet, which we already did).
    for x in range((len(commenterList)-1)):
        getFriendsOfUser(str(commenterList[x]), commenterList)

def printRelationships():
    """Print relationships fetched so far."""
    for x in range(len(relationshipList)):
        print("Friends from : -" + str(relationshipList[x][0]) + "- + -" + str(relationshipList[x][1]) + "-")

def writeResultsToCsv(aListRelationships,aFileName):
	"""Write relationships fetched into a csv file."""

    # Write file where each name is separated by a comma.
	with open(aFileName, 'w') as csvFile:
		aWriter = csv.writer(csvFile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
		for x in range(len(aListRelationships)):
			aWriter.writerow([aListRelationships[x][0],aListRelationships[x][1]])

def main():
    """Main function of the program."""

    # Id of the tweet. Uniquely identifies tweet of the specific user. This ID can be found at the end
    # of the URL of the tweet.
    aTweetID = 0

    # Username (or "twitter handle") of the Twitter user. Can also be found in the URL of the tweet.
    aUsername = ""
    getData(aTweetID,aUsername)

def getData(anID, aUsrnm):
    """Call all functions needed for fetching tweet data."""

    # Get all commenters in the tweet.
    commenterList = getCertainTweetAndComments(anID, aUsrnm)
    # Get who follows who in the tweet.
    getAllRelationships(aUsrnm, commenterList)
    # Save the relationship list in a csv file.
    writeResultsToCsv(relationshipList,"allRelationships.csv")

if __name__ == "__main__":
    main()
