import logging
import os

from config import MigrationConfig
from gitlab import Gitlab
import gitlab
from logging import getLogger, StreamHandler
import time
import pathlib

EXPORT_PATH = pathlib.Path('./tmp')

logger = getLogger('gitlab-group.migration-tool')
logger.addHandler(StreamHandler())
config = MigrationConfig('migration.cfg')
logger.setLevel(logging.INFO if config['default']['log_level'] == 'info' else logging.DEBUG)
dest_config = config['destination']

source_gitlab = Gitlab(url=dest_config.get('url'), private_token=dest_config.get('private_token'))


branch_to_protect = {
  "main": {
    "pushAccessLevel": 40,
    "mergeAccessLevel": 30
  },
  "master": {
    "pushAccessLevel": 40,
    "mergeAccessLevel": 30
  },
}


def main():
    source_group_id = dest_config.get('group_id')
    source_group = source_gitlab.groups.get(source_group_id)
    source_projects_iterator = source_group.projects.list(iterator=True)
    source_projects = list(source_projects_iterator)

    while source_projects_iterator.next_page:
        source_projects_iterator = (
            source_group.projects.list(iterator=True, page=source_projects_iterator.current_page + 1))
        source_projects.append(list(source_projects_iterator))

    for _project in source_projects:
        project = source_gitlab.projects.get(_project.id)
        for branch, merge_config in branch_to_protect.items():
            try:
                project.protectedbranches.delete(branch)
                project.protectedbranches.create({
                    'name': branch,
                    'merge_access_level': merge_config['mergeAccessLevel'],
                    'push_access_level': merge_config['pushAccessLevel'],
                    'allow_force_push': False
                })
                print(f"Branch {branch} of project {project.name} updated")
            except Exception as e:
                logger.error(e)


if __name__ == "__main__":
    logger.info("Start script")
    main()
