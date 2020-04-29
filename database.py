#!/usr/bin/env python
# -*- coding: utf-8 -*- 
"""Class to handle all database connections."""

import os
import mysql.connector as sql

import utils as ut

SQL_USER = os.getenv("SQL_USER")
SQL_PASS = os.getenv("SQL_PASS")

if SQL_USER is None or SQL_PASS is None:
    raise Exception("Cannot find required database login information")


class Database:

    def __enter__(self, *args, **kwargs):
        # Connect to the database

        self.db_config = {
            'host': '209.97.130.228',
            'port': 3306,
            'database': 'sheffieldcompsci',
            'user': SQL_USER,
            'password': SQL_PASS,
            'charset': 'utf8',
            'use_unicode': True,
            'get_warnings': True,
            'autocommit': True,
            'raise_on_warnings': False
        }

        self.connection = sql.Connect(**self.db_config)

        self.cursor = self.connection.cursor(dictionary=True)

        return self

    def __exit__(self, exception_type, value, traceback):
        self.connection.close()


async def create_tables():
    with Database() as db:
        query_list = (
            """
            CREATE TABLE IF NOT EXISTS
            USERS (
                ID INT NOT NULL AUTO_INCREMENT,
                name VARCHAR(255) NOT NULL,
                discordID VARCHAR(255) UNIQUE NOT NULL,
                jamming INT,
                PRIMARY KEY (ID)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS
            JAM_TEAM (
                ID INT NOT NULL AUTO_INCREMENT,
                teamName VARCHAR(255) NOT NULL UNIQUE,
                gitLink VARCHAR(255) NOT NULL UNIQUE,
                PRIMARY KEY (ID)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS
            JAM_TEAM_MEMBER (
                ID INT NOT NULL AUTO_INCREMENT,
                teamID INT NOT NULL,
                userID INT NOT NULL UNIQUE,
                creator INT NOT NULL DEFAULT 0,
                PRIMARY KEY (ID)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS
            EVENTS (
                ID INT NOT NULL AUTO_INCREMENT,
                title VARCHAR(255) NOT NULL,
                description VARCHAR(1024) NOT NULL,
                date DATETIME NOT NULL,
                creator INT NOT NULL,
                PRIMARY KEY (ID),
                FOREIGN KEY (creator)
                    REFERENCES USERS(ID)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS
            GUILDS (
                ID INT NOT NULL AUTO_INCREMENT,
                guildID VARCHAR(255) NOT NULL UNIQUE,
                registeringID VARCHAR(255) UNIQUE,
                memberID VARCHAR(255) UNIQUE,
                welcomeMessageID VARCHAR(255) UNIQUE,
                
                PRIMARY KEY(ID)
            )
            """
        )

        for query in query_list:
            try:
                db.cursor.execute(query)
            except sql.errors.ProgrammingError:
                ut.log_error(f"Query \n'{query}'\n raised an error, ensure that the "
                             "syntax is correct.")


async def add_user(discord_id, bot, name):
    with Database() as db:
        if bot:
            return
        try:
            db.cursor.execute(f"""
                INSERT INTO USERS (
                    name, discordID
                )
                VALUES (
                    %s,
                    %s
                )
            """, (name, discord_id))

            db.connection.commit()
            return db.cursor.lastrowid
        except sql.errors.IntegrityError:
            return False


async def get_user_id(discord_id):
    with Database() as db:
        db.cursor.execute(f"""
            SELECT ID FROM USERS
            WHERE discordID = %s
        """, (discord_id, ))

        result = db.cursor.fetchone()
        if result:
            return result['ID']

        result = await add_user(discord_id, False, "Unknown")
        return result


async def add_guild(guild_id, registering_id, member_id):
    with Database() as db:
        try:
            db.cursor.execute(f"""
                INSERT INTO GUILDS (
                    guildID, registeringID, memberID
                )
                VALUES (
                    %s,
                    %s,
                    %s
                )
            """, (guild_id, registering_id, member_id))

            db.connection.commit()
        except sql.errors.IntegrityError:
            pass


async def get_guild_info(guild_id, field="*"):
    # We use string formatting for field since it is only created internally
    # and if we used the same method as guild_id, it would be escaped.
    with Database() as db:
        db.cursor.execute(f"""
            SELECT {field} FROM GUILDS
            WHERE guildID = %s
        """, (guild_id,))

        result = db.cursor.fetchone()

        if field != "*" and result[field]:
            return int(result[field])
        if result:
            return result
        return False


async def set_guild_info(guild_id, field, new_value):
    # We use string formatting for field since it is only created internally
    # and if we used the same method as guild_id, it would be escaped.
    with Database() as db:
        try:
            db.cursor.execute(f"""
                UPDATE GUILDS
                SET {field} = %s
                WHERE guildID = %s
            """, (new_value, guild_id))

            db.connection.commit()
        except sql.errors.IntegrityError:
            return False


async def set_jamming(user_id, new_value):
    with Database() as db:
        db.cursor.execute(f"""
            UPDATE USERS
            SET jamming = %s
            WHERE discordID = %s
        """, (new_value, user_id))

        db.connection.commit()
        return True


async def get_user_jam_team(discord_id):
    with Database() as db:
        user_id = await get_user_id(discord_id)
        db.cursor.execute(f"""
            SELECT teamID FROM JAM_TEAM_MEMBER
            WHERE userID = %s
        """, (user_id,))

        result = db.cursor.fetchone()

        if result:
            return result['teamID']
        return False


async def add_user_jam_team(user_id, jam_team, creator="0"):
    with Database() as db:
        try:
            db.cursor.execute(f"""
                INSERT INTO JAM_TEAM_MEMBER
                (teamID, userID, creator)
                VALUES
                (%s, %s, %s)
            """, (jam_team, user_id, creator))

            db.connection.commit()
            return True
        except sql.errors.IntegrityError:
            return False


async def create_jam_team(discord_id, team_name, git_link):
    jam_team_id = await get_user_jam_team(discord_id)
    if jam_team_id:
        return False, "User is already a member of a team."
    with Database() as db:
        try:
            db.cursor.execute(f"""
                INSERT INTO JAM_TEAM
                (teamName, gitLink)
                VALUES
                (%s, %s)
            """, (team_name, git_link))

            jam_team = db.cursor.lastrowid
            user_id = await get_user_id(discord_id)
            await add_user_jam_team(user_id, jam_team, creator="1")
            db.connection.commit()
        except sql.errors.IntegrityError:
            return False, "Team name or git link already in use."


async def test_function():
    result = await get_user_id("247428233086238720")
    print(result)
    result = await get_user_jam_team("247428233086238720")
    print(result)
    result = await add_user_jam_team("7", "1", "1")
    print(result)
    result = await create_jam_team("247428233086238720", "The Lone Jammer", "https://git.com/LoneJammer")
    print(result)


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_function())
    loop.close()