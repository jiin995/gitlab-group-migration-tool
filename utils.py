def construct_git_url_with_credentials(project_url: str, username: str, password: str):
    return f'https://{username}:{password}@{project_url.split("//")[1]}'
