from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest
import sys
import csv
import traceback
import time
import re




client.connect()
if not client.is_user_authorized():
    client.send_code_request(phone)
    client.sign_in(phone, input('Enter verification code: '))

def add_users_to_group() -> None:
    """Add users from CSV to selected group"""
    input_file = sys.argv[1]
    users = []

    
    with open(input_file, encoding='UTF-8') as file:
        reader = csv.reader(file, delimiter=',', lineterminator='\n')
        next(reader)  # Skip header
        for row in reader:
            if len(row) < 3:
                print('Skipping incomplete user record')
                continue
            user = {
                'username': row[0],
                'id': int(row[1]) if row[1] else 0,
                'access_hash': int(row[2]) if row[2] else 0
            }
            users.append(user)

    
    result = client(GetDialogsRequest(
        offset_date=None,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=200,
        hash=0
    ))
    groups = [chat for chat in result.chats if getattr(chat, 'megagroup', False)]

 
    print('\nAvailable groups:')
    for idx, group in enumerate(groups):
        print(f'{idx}: {group.title}')
    group_idx = int(input('\nEnter group number: '))
    target_group = groups[group_idx]
    target_entity = InputPeerChannel(target_group.id, target_group.access_hash)

    
    add_method = int(input('\nAdd method (1-by username, 2-by ID): '))

    
    for user in users:
        try:
            print(f'Adding {user["username"]}')
            if add_method == 1:
                user_entity = client.get_input_entity(user['username'])
            elif add_method == 2:
                user_entity = InputPeerUser(user['id'], user['access_hash'])
            else:
                print('Invalid method')
                break

            client(InviteToChannelRequest(target_entity, [user_entity]))
            print('Waiting 60 seconds...')
            time.sleep(60)
        except PeerFloodError:
            print('Flood error. Stopping.')
            break
        except UserPrivacyRestrictedError:
            print('Privacy restrictions. Skipping.')
        except Exception as e:
            print(f'Error: {str(e)}')
            traceback.print_exc()

def list_users_in_group() -> None:
    """Export group members to CSV"""
    result = client(GetDialogsRequest(
        offset_date=None,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=200,
        hash=0
    ))

    
    print('\nAvailable chats:')
    for idx, chat in enumerate(result.chats):
        print(f'{idx}: {chat.title}')
    group_idx = int(input('\nEnter group number: '))
    target_group = result.chats[group_idx]

    
    print('Fetching members...')
    participants = client.get_participants(target_group, aggressive=True)

    
    sanitized_title = re.sub('[^a-z]+', '-', target_group.title.lower())
    filename = f'members-{sanitized_title}.csv'
    
    with open(filename, 'w', encoding='UTF-8') as file:
        writer = csv.writer(file, delimiter=',', lineterminator='\n')
        writer.writerow(['username', 'user_id', 'access_hash', 'name', 'group', 'group_id'])
        for user in participants:
            name = ' '.join(filter(None, [user.first_name, user.last_name]))
            writer.writerow([
                user.username or '',
                user.id,
                user.access_hash,
                name,
                target_group.title,
                target_group.id
            ])
    print(f'Saved {len(participants)} members to {filename}')

def display_csv() -> None:
    """Display CSV file contents"""
    with open(sys.argv[1], encoding='UTF-8') as file:
        reader = csv.reader(file, delimiter=',', lineterminator='\n')
        for row in reader:
            print(row)
    sys.exit('File display completed')


if __name__ == '__main__':
    print('\nTelegram Manager:')
    choice = int(input(
        '1. List group members\n'
        '2. Add users to group\n'
        '3. Display CSV contents\n'
        'Select option: '
    ))

    if choice == 1:
        list_users_in_group()
    elif choice == 2:
        add_users_to_group()
    elif choice == 3:
        display_csv()
    else:
        print('Invalid selection')
