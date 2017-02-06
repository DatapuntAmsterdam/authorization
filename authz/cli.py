"""
    authz.cli
    ~~~~~~~~~
"""
import sys
import click
import crayons
import psycopg2
from .map import AuthzMap
from . import levels

valid_levels = {
    l[6:]: getattr(levels, l) for l in dir(levels) if l[:6] == 'LEVEL_'
}


@click.group()
@click.option('--debug', is_flag=True)
@click.option('--psql-host', default='localhost', type=str, envvar='PSQL_HOST')
@click.option('--psql-port', default=5432, type=int, envvar='PSQL_PORT')
@click.option('--psql-db', type=str, envvar='PSQL_DB')
@click.option('--psql-user', type=str, envvar='PSQL_USER')
@click.option('--psql-password', type=str, prompt=True, hide_input=True, envvar='PSQL_PASSWORD')
@click.pass_context
def cli(ctx, debug, psql_host, psql_port, psql_db, psql_user, psql_password):
    try:
        authzmap = AuthzMap(
            host=psql_host,
            port=psql_port,
            dbname=psql_db,
            user=psql_user,
            password=psql_password
        )
    except psycopg2.OperationalError as e:
        print(crayons.red('Could not connect to the database'))
        if debug:
            raise
        sys.exit(1)
    # create the tables if they don't exist
    authzmap.create()
    ctx.authzmap = authzmap


@cli.group()
@click.argument('user', type=str)
@click.pass_context
def user(ctx, user):
    ctx.user = user
    ctx.authzmap = ctx.parent.authzmap


@user.command()
@click.argument('level', type=click.Choice(valid_levels.keys()))
@click.pass_context
def assign(ctx, level):
    authzmap = ctx.parent.authzmap
    user = ctx.parent.user
    try:
        authzmap[user] = valid_levels[level]
    except ValueError:
        if user in authzmap:
            del authzmap[user]
    print(crayons.green('User {} now has authz level {}'.format(user, level)))


@user.command()
@click.pass_context
def info(ctx):
    authzmap = ctx.parent.authzmap
    user = ctx.parent.user
    if user in authzmap:
        l = authzmap[user]
        level = [k for k in valid_levels if valid_levels[k] == l][0]
        print(crayons.green('User {} has authorization level {}'.format(user, level)))
    else:
        print(crayons.green('User {} has default authorization level'.format(user)))


if __name__ == '__main__':
    cli()
