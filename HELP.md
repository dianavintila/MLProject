# Learn more about the project

## Run the project

1. Generate collusion facts for specific APK file:
```
python2 generate_facts.py -v -a /path/to/app.apk
sudo python2 generate_facts.py -d /home/kali/Desktop/apk -v 
```
2. Generate prolog program using previously generated collusion facts 
```
python2 generate_prolog.py -v
```
3. Detect collusion only for app sets that start with a specific app package:
```
python2 detect_collusion.py -a APP_PACKAGE prolog_program_filename collusion_kind
```
```
collusion_kind: colluding_info, colluding_money1, colluding_money2, colluding_service, colluding_camera, colluding_accounts, colluding_sms
```
