import pymysql.cursors
import config


class Criteria():
    def __init__(self, fields_dict=None, fields_join='AND'):
        self.search_condition = ''
        self.search_values = []
        if fields_dict:
            self.add_search(fields_dict, fields_join)

    def __get_sql_lists(self, fields_dict):
        values = []
        search = []
        for k, v in fields_dict.items():
            search.append("`%s` LIKE " % k + "%s")
            values.append(v)
        return values, search

    def get_search_params(self):
        return self.search_values, self.search_condition

    def __add(self, values, search, fields_join='AND', prev_cond_join='AND'):
        search_srt = (" %s " % fields_join).join(search)
        if self.search_condition:
            self.search_condition += " %s " % prev_cond_join
        self.search_values += values
        self.search_condition += "(%s)" % search_srt

    def add_search(self, fields_dict, fields_join='AND', prev_cond_join='AND'):
        values, search = self.__get_sql_lists(fields_dict)
        self.__add(values, search, fields_join, prev_cond_join)

    def add_condition(self, cond, fields_join='AND', prev_cond_join='AND'):
        values = [cond[2]]
        search = ["`%s` %s " % cond[0:2] + "%s"]
        self.__add(values, search, fields_join, prev_cond_join)

    def add_conditions(self, conds, fields_join='AND', prev_cond_join='AND'):
        for cond in cons:
            self.add_condition(cond, fields_join, prev_cond_join)


class Database():
    def __init__(self):
        self.db_con = pymysql.connect(host=config.db['host'],
                                      user=config.db['user'],
                                      password=config.db['password'],
                                      db=config.db['db'],
                                      charset=config.db['charset'],
                                      cursorclass=pymysql.cursors.DictCursor)

    def __execute(self, sql, values=(), rowcount=False, find_one=False, find_all=False, get_id=False):
        result = True
        try:
            with self.db_con.cursor() as cursor:
                cursor.execute(sql, values)
                if rowcount:
                    result = cursor.rowcount
                if find_one:
                    result = cursor.fetchone()
                if find_all:
                    result = cursor.fetchall()
                if get_id:
                    result = cursor.lastrowid
            self.db_con.commit()
        except pymysql.Error as err:
            print("DB error!", err)
            result = None
            self.db_con.rollback()
        return result

    def __get_sql_strings(self, criteria):
        if not isinstance(criteria, Criteria):
            criteria = Criteria(criteria)
        return criteria.get_search_params()

    def __find(self, table, criteria, rowcount=False, find_one=False, find_all=False, search_cont_join='AND'):
        values, search = self.__get_sql_strings(criteria)
        sql = "SELECT * FROM `%s` WHERE %s" % (table, search)
        return self.__execute(sql, values, rowcount=rowcount, find_one=find_one, find_all=find_all)

    def delete(self, table, criteria):
        values, search = self.__get_sql_strings(criteria)
        sql = "DELETE FROM `%s` WHERE %s" % (table, search)
        return self.__execute(sql, values, rowcount=True)

    def insert(self, table, fields_dict):
        fields_str = ", ".join(["`%s`" % f for f in fields_dict.keys()])
        val_str = ", ".join(['%s'] * len(fields_dict))
        sql = "INSERT INTO `%s` (%s) VALUES (%s)" % (table, fields_str, val_str)
        return self.__execute(sql, list(fields_dict.values()), get_id=True)

    def update(self, table, criteria, fields_dict):
        search_values, search = self.__get_sql_strings(criteria)
        fields_to_update = []
        all_values = []
        for k, v in fields_dict.items():
            fields_to_update.append(k + ' = %s')
            all_values.append(v)
        all_values += search_values
        sql = "UPDATE `%s` SET %s WHERE %s" % (table, ', '.join(fields_to_update), search)
        return self.__execute(sql, all_values, rowcount=True)

    def find_one(self, table, criteria, search_cont_join='AND'):
        return self.__find(table, criteria, find_one=True, search_cont_join=search_cont_join)

    def find_many(self, table, criteria, count='all', search_cont_join='AND'):
        find_all = True if count == 'all' else False
        return self.__find(table, criteria, find_all=find_all, search_cont_join=search_cont_join)

    def count(self, table, criteria):
        return self.__find(table, criteria, rowcount=True)
