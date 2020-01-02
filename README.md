# Alexandria public version

Bot for LO server management. Keep in mind this code is usually the older version of current version in server.

## Requirements:
    Python >=3.7
    Pendulum
    Discord.py 
    Asyncpg (use whatever you use for db, as long as it is asyncronous.)
    
## Config file
In order to use this bot you need to create a **CONFIG.py** file in project root folder.

#### Prefix
Defines the prefix that the bot will recognize for cmds.

`PREFIX = "?"`


#### Token
`TOKEN = "Your bot token here"`

#### Database Config
Basic database stuff, feel free to change. In this case, postgres.

```
USERNAME = 'username'
PASSWORD = 'password'
DATABASE = 'database'
```
