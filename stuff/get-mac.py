from getmac import get_mac_address
mac = get_mac_address()
print(f'mac: {mac}')


#  python3 -c 'import getmac ; print("mac:", getmac.get_mac_address().replace(":",""))'
#  python3 -c 'import getmac ; print("pi-"+getmac.get_mac_address().replace(":",""))'
