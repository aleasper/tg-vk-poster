from getpass import getpass

def get_vk_creds():
    login = input('Enter VK login: ')
    password = getpass('Enter VK password: ')
    return login, password

def auth_vk_handler():
    key = input("Enter VK authentication code: ")
    remember_device = True
    return key, remember_device

def get_user_channel_select(channels):
    for case in [f'{ch}: {channels[ch]["name"]}' for ch in channels]:
        print(case)
    channel_index = int(input("Enter index: "))
    print(f'Selected channel is: {channels[channel_index]["name"]}')
    return channels[channel_index]