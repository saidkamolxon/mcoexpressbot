import sqlite3


class CoreSQL:
    def __init__(self, path_to_db='main.db') -> None:
        self.path_to_db = path_to_db

    @property
    def connection(self):
        return sqlite3.connect(self.path_to_db)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = ()
        connection = self.connection
        connection.set_trace_callback(logger)
        cursor = connection.cursor()
        cursor.execute(sql, parameters)
        data = cursor.rowcount

        if commit:
            connection.commit()
        if fetchall:
            data = cursor.fetchall()
        if fetchone:
            data = cursor.fetchone()
        connection.close()
        return data

    def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users(
            user_id VARCHAR(16),
            name VARCHAR(256),
            is_admin BOOLEAN,
            PRIMARY KEY(user_id)
        );
"""
        self.execute(sql, commit=True)

    def create_table_groups(self):
        sql = """CREATE TABLE IF NOT EXISTS groups(
            id INTEGER AUTOINCREMENT,
            name TEXT UNIQUE,
            PRIMARY KEY(id)
        );
"""
        self.execute(sql, commit=True)

    def create_table_facilities(self):
        sql = """CREATE TABLE IF NOT EXISTS facilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        address TEXT
);
"""
        self.execute(sql, commit=True)

    def create_table_chats(self, group):
        sql = f"""
        CREATE TABLE IF NOT EXISTS '{group}'(
        chat_id TEXT,
        title TEXT,
        PRIMARY KEY(chat_id)
        );
"""
        self.execute(sql, commit=True)

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join([
            f"{item} = ?" for item in parameters
        ])
        return sql, tuple(parameters.values())

    # region GETTING --->>> ###

    def get_users(self, only_admins=False):
        sql: str = """
        SELECT user_id, name FROM users
        """
        if only_admins:
            sql += " WHERE is_admin = 1"
        data = self.execute(sql, fetchall=True)
        return {user_id: name for user_id, name in data}

    def get_groups(self):
        sql = "SELECT * FROM groups"
        data = self.execute(sql, fetchall=True)
        return {f'gr_{i[0]}': i[1] for i in data}

    def get_chats(self, group: str) -> dict | int:
        sql = f"""
        SELECT * FROM '{group}' WHERE is_active = 1
        """
        try:
            data = self.execute(sql, fetchall=True)
            return {i[0]: i[1] for i in data}
        except:
            return -1

    # endregion

    # region ADDING --->>> ###

    def add_to_users(self, user_id, name, is_admin=False):
        # SQL_EXAMPLE = "INSERT INTO users VALUES(1, 'John', Null)
        is_admin = '1' if is_admin else ''
        sql = """
        INSERT INTO users VALUES(?, ?, ?)
        """
        try:
            self.execute(sql, parameters=(user_id, name, is_admin), commit=True)
        except:
            pass

    def add_a_group(self, group_name: str):
        self.create_table_groups()
        sql = """
        INSERT INTO groups(name) VALUES(?)
        """
        self.execute(sql, parameters=tuple(group_name))

    def add_to_facilities(self, facility: str, address: str):
        '''This function adds the given facility to the await db. If it is found,
        so it will update that facility...'''
        sql = """
        UPDATE facilities SET address = ? WHERE name = ?;
        """
        r = self.execute(sql, parameters=(address, facility), commit=True)
        if not r:
            sql = """
            INSERT INTO facilities(name, address) VALUES(?, ?)
            """
            self.execute(sql, parameters=(facility, address), commit=True)

    def add_to_chats(self, group: str, chat_id: str, chat_title: str) -> None:
        """This func adds the given chat one of the group of chats"""
        self.create_table_chats(group)
        sql = f"""
        INSERT INTO '{group}' 
        VALUES('{chat_id}',
               '{chat_title}',
               1)         
"""
        try:
            self.execute(sql, commit=True)
        except:
            pass

    # endregion

    def make_an_admin(self, user_id: str) -> str:
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
        self.execute(sql, commit=True)
        return 'Done. The user is an admin now.'

    # region REMOVING --->>> ###

    def remove_from_users(self, user_id: str):
        """This func removes the given id from the users list"""
        if user_id not in self.get_users():
            return 'Not found any user with such id.'
        sql = f"""
        DELETE FROM users
        WHERE user_id = '{user_id}'
"""
        self.execute(sql, commit=True)
        return 'Successfully removed.'

    def remove_from_chats(self, group: str, chat_id: str) -> str:
        """This func removes the given chat from the chats list"""
        if chat_id not in self.get_chats(group):
            return 'Not found any chat with such id.'
        sql = f"""
        DELETE FROM '{group}'
        WHERE chat_id = '{chat_id}'
"""
        self.execute(sql, commit=True)
        return 'Successfully removed.'

    def remove_from_all_chats(self, chat_id: str) -> None:
        groups = self.get_groups()
        for group in groups.values():
            self.remove_from_chats(group, chat_id)

    def set_on_off(self, chat_id, on: bool) -> str:
        groups = self.get_groups()
        for group in groups.values():
            sql = f"""
            UPDATE '{group}'
            SET is_active = {'1' if on else 'Null'}
            WHERE chat_id = '{chat_id}'
"""
            count = self.execute(sql, commit=True)
            if count == 1:
                return f"Successfully {'de' if not on else ''}activated."
        return 'Not found'


    def get_trucks(self) -> list:
        sql = """
        SELECT *
        FROM trucks
        WHERE chat_id != 'None';
        """
        result: list = self.execute(sql, fetchall=True)
        return result


def logger(statement):
    pass
#     print(f"""
# ------------------------------------------------------
# Executing:
# {statement}
# ------------------------------------------------------
# """)