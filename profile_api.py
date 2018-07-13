import requests, json
from config import app_token, master_token

DEBUG = False

def send_query(data, url = 'https://profile.goto.msk.ru/graphql'):
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        data = json.dumps({"query": data})
        if DEBUG:
            print("data sent: ", data)
        answer = requests.post(url, data=data, headers=headers)
        if DEBUG:
            print("data returned: ", answer.text)
        return  answer.json()
    except:
        return None

def get_token_by_telegram(name):
    data = '''
            {
              getTokenByTelegram(applicationToken: "%s", telegram: "%s")
            }
        ''' % (app_token, name)
    result = send_query(data)

    try:
        return result['data']['getTokenByTelegram']
    except:
        return None


def get_balance_by_token(token):
    data = '''
        {
          getUserInformation(token: "%s"){
            gotoCoins
          }
        }
    '''  % token
    result = send_query(data)
    try:
        return result['data']['getUserInformation']['gotoCoins']
    except:
        return None

def get_id_by_token(token):
    data = '''
        {
          getUserInformation(token: "%s"){
            profileId
          }
        }
    '''  % token
    result = send_query(data)
    try:
        return result['data']['getUserInformation']['profileId']
    except:
        return None

def get_name_by_id(id):
    data = '''
        {
          getUserInformation(userId: %s){
            firstName
            lastName
          }
        }
    '''  %id
    result = send_query(data)
    try:
        return result['data']['getUserInformation']['firstName'] + " " +result['data']['getUserInformation']['lastName']
    except:
        return None

def submit_gotocoins(token, id, amount, comment):
    data = '''
        {
          newGoToCoinTransaction(token: "%s", comment: "%s", count: %s, profileId: "%s")
        }
    '''  % (token, comment, amount, id)
    result = send_query(data)
    try:
        return result['data']['newGoToCoinTransaction'] == True
    except:
        return False

def get_permissions_by_token(token):
    data = '''
        {
          getUserInformation(token: "%s"){
            permissions
          }
        }
    '''  % token
    result = send_query(data)
    try:
        return result['data']['getUserInformation']['permissions'].lower() in ['администратор', 'преподаватель', 'организатор']
    except:
        return False

def get_history_by_token(token):
    data = '''
    {
         getGoToCoinTransactions(token: "%s"){
            userFrom{
              firstName
              lastName
              middleName
              profileId
              telegram
            }
            count
            comment
        }
    }
    '''  % token
    result = send_query(data)
    try:
        return result['data']['getGoToCoinTransactions']
    except:
        return []

def get_students_by_token(token):
    data = '''
        {
          getRelatedFormAnswers(token: "%s") {
            name
            user {
              profileId
              firstName
              lastName
              gotoCoins
            }
          }
        }
    '''  % token
    result = send_query(data)
    try:
        return result['data']['getRelatedFormAnswers']
    except:
        return []

if __name__ == "__main__":
    DEBUG = True
    token = get_token_by_telegram("roctbb")
    print(get_balance_by_token(token))
    print(get_permissions_by_token(token))
    print(get_students_by_token(token))
    print(get_name_by_id(102))
    print(get_id_by_token(token))
    print(submit_gotocoins(master_token, 102, 2, 'test'))
    print(get_history_by_token(token))
