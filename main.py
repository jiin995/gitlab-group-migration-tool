import logging
import os

from config import MigrationConfig
from gitlab import Gitlab
from logging import getLogger, StreamHandler
import time
import pathlib
from utils import construct_git_url_with_credentials

EXPORT_PATH = pathlib.Path('./tmp')

logger = getLogger('gitlab-group.migration-tool')
logger.addHandler(StreamHandler())
config = MigrationConfig('migration.cfg')
logger.setLevel(logging.INFO if config['default']['log_level'] == 'info' else logging.DEBUG)
source_config = config['source']
dest_config = config['destination']

source_gitlab = Gitlab(url=source_config.get('url'), private_token=source_config.get('private_token'))

destination_gitlab = Gitlab(url=dest_config.get('url'), private_token=dest_config.get('private_token'))
migrate_strategy = config['default'].get('migrate_strategy')
os.makedirs(EXPORT_PATH.resolve(), exist_ok=True)

replica_strategy = config['default'].get('replica', 'none')


def main():
    source_group_id = source_config.get('group_id')
    source_group = source_gitlab.groups.get(source_group_id)
    source_projects_iterator = source_group.projects.list(iterator=True)
    source_projects = list(source_projects_iterator)

    while source_projects_iterator.next_page:
        source_projects_iterator = (
            source_group.projects.list(iterator=True, page=source_projects_iterator.current_page + 1))
        source_projects.append(list(source_projects_iterator))
    logger.info(f"Ready to import {len(source_projects)} projects with strategy: {migrate_strategy}")
    destination_group = destination_gitlab.groups.get(dest_config.get('group_id'))
    for _project in source_projects:
        try:
            source_project = source_gitlab.projects.get(_project.id)
            logger.info(f"[{source_project.name}]: Start migration with strategy: {migrate_strategy} ")
            if migrate_strategy == 'import-url':
                import_project_url = construct_git_url_with_credentials(source_project.http_url_to_repo,
                                                                        source_config.get("username"),
                                                                        source_config.get("private_token"))
                destination_project = destination_gitlab.projects.create({
                    'name': source_project.name,
                    'import_url': import_project_url,
                    'ci_cd_only': False,
                    'selected_namespace_id': dest_config.get('group_id'),
                    'namespace_id': dest_config.get('group_id'),
                    'path': source_project.path,
                    'visibility_level': 0,

                })
            elif migrate_strategy == 'export-import':
                export = source_project.exports.create()

                # Wait for the 'finished' status
                export.refresh()
                logger.info(f"[{source_project.name}]: Start export")
                while export.export_status != 'finished':
                    logger.debug(f"[{source_project.name}]: Waiting export")
                    time.sleep(1)
                    export.refresh()
                logger.info(f"[{source_project.name}]: Export finished")
                # Download the result
                export_path = EXPORT_PATH.joinpath(f'{source_project.name}.tgz')
                with open(export_path, 'wb') as f:
                    export.download(streamed=True, action=f.write)
                with open(export_path, 'rb') as f:
                    output = destination_gitlab.projects.import_project(
                        f, path=source_project.path, name=source_project.name, namespace=destination_group.full_path
                    )

                # Get a ProjectImport object to track the import status
                destination_project = destination_gitlab.projects.get(output['id'])
                destination_project_import = destination_project.imports.get()
                logger.info(f"[{destination_project.name}]: Start import")
                while destination_project_import.import_status != 'finished':
                    logger.debug(f"[{destination_project.name}]: Waiting import")
                    time.sleep(1)
                    destination_project_import.refresh()
                logger.info(f"[{destination_project.name}]: Import finished")
            logger.info(f'[{source_project.name}]: migrated, new url {destination_project.http_url_to_repo}')
            if replica_strategy == 'destination-to-source':
                logger.info(f'[{source_project.name}]: Replica from {destination_project.http_url_to_repo} to {source_project.http_url_to_repo} configured')
                source_project_url = construct_git_url_with_credentials(source_project.http_url_to_repo,
                                                                        source_config.get("username"),
                                                                        source_config.get("private_token"))
                destination_project.remote_mirrors.create({
                    'url': source_project_url,
                    'enabled': True})

            elif replica_strategy == 'source-to-destination':
                logger.info(f'[{source_project.name}]: Replica from {source_project.http_url_to_repo} to {destination_project.http_url_to_repo} configured')
                destination_project_url = construct_git_url_with_credentials(destination_project.http_url_to_repo,
                                                                             dest_config.get("username"),
                                                                             dest_config.get("private_token"))
                source_project.remote_mirrors.create({
                    'url': destination_project_url,
                    'enabled': True})

            elif replica_strategy == 'both':
                destination_project_url = construct_git_url_with_credentials(destination_project.http_url_to_repo,
                                                                             dest_config.get("username"),
                                                                             dest_config.get("private_token"))
                source_project.remote_mirrors.create({
                    'url': destination_project_url,
                    'enabled': True})

                source_project_url = construct_git_url_with_credentials(source_project.http_url_to_repo,
                                                                        source_config.get("username"),
                                                                        source_config.get("private_token"))
                destination_project.remote_mirrors.create({
                    'url': source_project_url,
                    'enabled': True})
                logger.info(f'[{source_project.name}]: Replica from {source_project.http_url_to_repo} to {destination_project.http_url_to_repo} and vice versa configured')

            else:
                logger.debug(f'[{source_project.name}]: Skip replica config')
            time.sleep(0.2)
        except Exception as e:
            logger.error(e)


if __name__ == "__main__":
    logger.info("Start migration")
    main()
