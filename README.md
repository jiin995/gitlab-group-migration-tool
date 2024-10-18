# Gitlab Group Migration Tool

<a name="readme-top"></a>

## 📗 Table of Contents

- [📖 About the Project](#about-project)
  - [✨ Features](#features)
  - [♟️ Migration Strategies](#migration-strategies)
  - [Replica](#replica)
- [⚒️ Usage](#usage)
- [👥 Authors](#authors)
- [❓ FAQ](#faq)


## 📖 About the Project <a name="about-project"></a>
Tool to migrate one gitlab group to another.

### ✨ Features <a name="features"></a>
- Cross instance migration
- No administrator permission required
- Support replica configuration between repos
- Work without direct sync

### ♟️ Migration Strategies <a name="migration-strategies"></a>

The script support 2 migration strategies:

- export-import: export from source and import to destination
- import-url: create new project in destination group using import with git url

### Replica <a name="replica"></a>
 
Using the config parameter **replica** the script autoconfigure replica from repositories.
Allowed values are:
- source-to-destination: enable replica from destination repository to source
- destination-to-source: enable replica from source repository to destination 
- both: enable replica from destination repository to source and vice versa

Note: the script use source or destination token for configure replica. For use replica the source or destination or both
tokens need to be scope **write_repository** 

## ⚒️ Usage <a name="usage"></a>

1. Generate access tokens for source and destination gitlab instances
2. Install requirements with: `pip install -r requirements.txt`
3. Create configuration file with: `cp example_migration.cfg migration.cfg`
4. Configure variables in **migration.cfg**
5. Run with: `python3 main.py`

## 👥 Authors <a name="authors"></a>
- **Gabriele Previtera**: [@jiin995](https://gitlab.com/jiin995)
