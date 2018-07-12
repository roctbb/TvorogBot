import requests, json
from config import app_token


def send_query(data, url = 'https://profile.goto.msk.ru/graphql'):
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        data = json.dumps({"query": data})
        print("data sent: ", data)
        answer = requests.post(url, data=data, headers=headers)
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

if __name__ == "__main__":
    token = get_token_by_telegram("roctbb")
    print(get_balance_by_token(token))
    print(get_permissions_by_token(token))
