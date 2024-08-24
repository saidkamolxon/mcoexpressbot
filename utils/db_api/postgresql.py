import asyncpg
import logging
from typing import Union
from asyncpg import Connection
from asyncpg.pool import Pool
from data.config import DB_USER, DB_PASS, DB_HOST, DB_NAME, DB_PORT
from utils.common_functions import get_current_time, get_converted_date


class CoreSQL:
    def __init__(self):
        self.pool: Union[Pool, None] = None

    async def create(self):
        self.pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            database=DB_NAME,
            port=DB_PORT
        )

    async def execute(self, command, *args,
                      fetchall: bool = False,
                      fetchval: bool = False,
                      fetchone: bool = False,
                      execute: bool = False):
        async with self.pool.acquire() as connection:
            connection: Connection
            async with connection.transaction():
                if fetchall:
                    result = await connection.fetch(command, *args)
                elif fetchval:
                    result = await connection.fetchval(command, *args)
                elif fetchone:
                    result = await connection.fetchrow(command, *args)
                elif execute:
                    result = await connection.execute(command, *args)
                return result

    async def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
        user_id VARCHAR(16) PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        is_admin BOOLEAN
        );
"""
        await self.execute(sql, execute=True)

    async def create_table_groups(self):
        sql = """CREATE TABLE IF NOT EXISTS groups(
            id INTEGER AUTOINCREMENT,
            name TEXT UNIQUE,
            PRIMARY KEY(id)
        );
"""
        await self.execute(sql)

    async def create_table_facilities(self):
        sql = """CREATE TABLE IF NOT EXISTS facilities (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE,
        address TEXT
);
"""
        await self.execute(sql, execute=True)

    async def create_table_chats(self, group):
        sql = f"""
        CREATE TABLE IF NOT EXISTS '{group}'(
        chat_id TEXT,
        title TEXT,
        PRIMARY KEY(chat_id)
        );
"""
        await self.execute(sql, execute=True)

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join([
            f"{item} = ${num}" for num, item in enumerate(parameters.keys(), start=1)
        ])
        return sql, tuple(parameters.values())

    async def add_user(self, user_id, full_name, username, is_admin=False):
        sql = """
        INSERT INTO users(
        user_id, full_name, username, is_admin)
        VALUES($1, $2, $3, $4) returning *
        """
        try:
            return await self.execute(sql, user_id, full_name, username, is_admin, fetchone=True)
        except Exception as ex:
            logging.error(ex)

    async def get_users(self, only_admins=False):
        sql = "SELECT user_id, name FROM users"
        if only_admins:
            sql += " WHERE is_admin = true"
        data = await self.execute(sql, fetchall=True)
        return {user_id: name for user_id, name in data}

    async def get_user(self, **kwargs):
        sql = "SELECT * FROM users WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchone=True)

    async def get_groups(self):
        sql = "SELECT * FROM groups"
        data = await self.execute(sql, fetchall=True)
        return {f'gr_{i[0]}': i[1] for i in data}

    async def get_chats(self, group: str) -> Union[dict, int]:
        sql = f"""
        SELECT * FROM "{group}" WHERE is_active = true
        """
        try:
            data = await self.execute(sql, fetchall=True)
            return {i[0]: i[1] for i in data}
        except Exception as ex:
            logging.error(ex)
            return -1

    # region ADDING --->>> ###

    async def add_to_users(self, user_id, name, is_admin=False):
        # SQL_EXAMPLE = "INSERT INTO users VALUES(1, 'John', Null)
        sql = f"""
        INSERT INTO users(user_id, name, is_admin) VALUES('{user_id}', '{name}', {is_admin});
"""
        try:
            return await self.execute(sql, execute=True)
        except Exception as ex:
            logging.error(ex)

    async def add_a_group(self, group_name: str):
        await self.create_table_groups()
        sql = f"""
        INSERT INTO groups(name) VALUES('{group_name}');
"""
        await self.execute(sql, execute=True)

    async def add_to_facilities(self, facility: str, address: str, points: str,
                                city: str, state: str, zip_code: str, coordinates: str):
        """This function adds the given facility to the await db. If it is found,
        so it will update that facility..."""
        sql = f"""
        UPDATE
            facilities
        SET 
            address = '{address}',
            points = '{points}',
            city = '{city}',
            state = '{state}',
            zip = '{zip_code}',
            coordinates = '{coordinates}'
        WHERE
            name = '{facility}';
"""
        r: str = await self.execute(sql, execute=True)
        if '0' in r:
            sql = f"""
            INSERT INTO 
                facilities(name, address, points, city, state, zip, coordinates) 
            VALUES('{facility.upper()}', '{address}', '{points}', '{city}', '{state}', '{zip}', '{coordinates}');
"""
            await self.execute(sql, execute=True)

    async def update_trailers(self, name: str, coordinates: str, location: str,
                              landmark: str = '', is_moving: bool = False,
                              last_event: str = '', last_update: str = ''):

        address = location.replace("'", "-") if "'" in location else location

        sql = f"""
        UPDATE
            trailers
        SET 
            coordinates = '{coordinates}',
            location = '{address}',
            landmark = '{landmark}',
            is_moving = '{is_moving}',
            last_event = '{last_event}',
            last_update = '{last_update}'
        WHERE
            name = '{name}'
            AND
            (
                last_event IS NULL
                OR CAST(last_event AS TIMESTAMP) <= CAST('{last_event}' AS TIMESTAMP)
            );
"""
        await self.execute(sql, execute=True)

    async def add_to_chats(self, group: str, chat_id: str, chat_title: str) -> None:
        """This func adds the given chat one of the group of chats"""
        await self.create_table_chats(group)
        sql = f"""
        INSERT INTO {group} 
        VALUES('{chat_id}',
               '{chat_title}',
               true)         
"""
        try:
            await self.execute(sql, execute=True)
        except Exception as ex:
            logging.error(ex)

    # endregion

    async def make_an_admin(self, user_id: str) -> str:
        """This func makes the given id an admin"""
        if user_id not in self.get_users():
            return 'Not found any user with such id.'
        if user_id in self.get_users(only_admins=True):
            return 'The user is already an admin'
        sql = f"""
        UPDATE users
        SET is_admin = 1
        WHERE user_id = '{user_id}';
"""
        await self.execute(sql, execute=True)
        return 'Done. The user is an admin now.'

    # region REMOVING --->>> ###

    async def remove_from_users(self, user_id: str):
        """This func removes the given id from the users list"""
        if user_id not in self.get_users():
            return 'Not found any user with such id.'
        sql = f"""
        DELETE FROM users
        WHERE user_id = '{user_id}'
"""
        await self.execute(sql, execute=True)
        return 'Successfully removed.'

    async def remove_from_chats(self, group: str, chat_id: str) -> str:
        """This func removes the given chat from the chats list"""
        if chat_id not in self.get_chats(group):
            return 'Not found any chat with such id.'
        sql = f"""
        DELETE FROM '{group}'
        WHERE chat_id = '{chat_id}'
"""
        await self.execute(sql, execute=True)
        return 'Successfully removed.'

    async def remove_from_all_chats(self, chat_id: str) -> None:
        groups = await self.get_groups()
        for group in groups.values():
            await self.remove_from_chats(group, chat_id)

    async def set_on_off(self, chat_id, on: bool) -> str:
        groups = await self.get_groups()
        for group in groups.values():
            sql = f"""
            UPDATE '{group}'
            SET is_active = {'1' if on else 'Null'}
            WHERE chat_id = '{chat_id}'
"""
            count = self.execute(sql, execute=True)
            if count == 1:
                return f"Successfully {'de' if not on else ''}activated."
        return 'Not found'

    async def get_trucks(self) -> list:
        sql = """
        SELECT *
        FROM trucks
        WHERE chat_id != 'None';
"""
        result: list = await self.execute(sql, fetchall=True)
        return result

    async def get_landmarks(self):
        facilities = dict()
        try:
            data = await self.execute("SELECT name, address FROM facilities;", fetchall=True)
        except Exception as ex:
            logging.error(ex)
            return -1
        else:
            for fac, add in data:
                facilities[fac] = {'address': add}
            return facilities

    async def get_trailer(self, trailer_name: str):
        sql = f"""
        SELECT
            name, coordinates, location, landmark, is_moving, last_event, last_update
        FROM 
            trailers
        WHERE
            name LIKE '%{trailer_name}%'
"""
        result = await self.execute(sql, fetchone=True)
        if not result:
            return -1
        trl = dict()
        trl['name'], trl['coordinates'], trl['location'], trl['landmark'], trl['is_moving'] = result[:5]
        trl['last_event'] = await get_converted_date(result[5])
        trl['last_update'] = await get_converted_date(result[6])
        return trl

    async def get_landmark(self, landmark_name: str):
        sql = f"""
        SELECT
            name, address, coordinates
        FROM
            facilities
        WHERE
            name LIKE '%{landmark_name}%';
"""
        result = await self.execute(sql, fetchall=True)
        if not result:
            return -1
        return list(result)

    async def get_trailers_by_landmark(self, landmark: str):
        sql = f"""
        SELECT
            name, coordinates
        FROM
            trailers
        WHERE
            landmark = '{landmark}'
        ORDER BY
            name
"""
        result = await self.execute(sql, fetchall=True)
        if not result:
            return -1
        return list(result)

    async def get_all_trailers(self):
        current_est_time = await get_current_time()
        sql = f"""
        SELECT
            name, is_moving, landmark, location, coordinates
        FROM
            trailers
        WHERE
            last_update IS NOT NULL
            OR
            CAST(last_update AS TIMESTAMP) + INTERVAL '3 days' < CAST('{current_est_time}' AS TIMESTAMP) 
        ORDER BY
            name
"""
        result = await self.execute(sql, fetchall=True)
        if not result:
            return -1
        return list(result)
