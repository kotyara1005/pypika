import unittest
from collections import OrderedDict

from pypika import (
    JSON,
    Table,
)
from pypika.dialects import PostgreSQLQuery


class InsertTests(unittest.TestCase):
    table_abc = Table("abc")

    def test_array_keyword(self):
        q = PostgreSQLQuery.into(self.table_abc).insert(1, [1, "a", True])

        self.assertEqual("INSERT INTO \"abc\" VALUES (1,ARRAY[1,'a',true])", str(q))


class JSONObjectTests(unittest.TestCase):
    def test_json_value_from_dict(self):
        q = PostgreSQLQuery.select(JSON({"a": "foo"}))

        self.assertEqual('SELECT \'{"a":"foo"}\'', str(q))

    def test_json_value_from_array_num(self):
        q = PostgreSQLQuery.select(JSON([1, 2, 3]))

        self.assertEqual("SELECT '[1,2,3]'", str(q))

    def test_json_value_from_array_str(self):
        q = PostgreSQLQuery.select(JSON(["a", "b", "c"]))

        self.assertEqual('SELECT \'["a","b","c"]\'', str(q))

    def test_json_value_from_dict_recursive(self):
        q = PostgreSQLQuery.select(JSON({"a": "z", "b": {"c": "foo"}, "d": 1}))

        # gotta split this one up to avoid the indeterminate order
        sql = str(q)
        start, end = 9, -2
        self.assertEqual("SELECT '{}'", sql[:start] + sql[end:])

        members_set = set(sql[start:end].split(","))
        self.assertSetEqual({'"a":"z"', '"b":{"c":"foo"}', '"d":1'}, members_set)


class JSONOperatorsTests(unittest.TestCase):
    # reference https://www.postgresql.org/docs/9.5/functions-json.html
    table_abc = Table("abc")

    def test_get_json_value_by_key(self):
        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.json.get_json_value("dates"))
        )

        self.assertEqual('SELECT * FROM "abc" WHERE "json"->\'dates\'', str(q))

    def test_get_json_value_by_index(self):
        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.json.get_json_value(1))
        )

        self.assertEqual('SELECT * FROM "abc" WHERE "json"->1', str(q))

    def test_get_text_value_by_key(self):
        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.json.get_text_value("dates"))
        )

        self.assertEqual('SELECT * FROM "abc" WHERE "json"->>\'dates\'', str(q))

    def test_get_text_value_by_index(self):
        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.json.get_text_value(1))
        )

        self.assertEqual('SELECT * FROM "abc" WHERE "json"->>1', str(q))

    def test_get_path_json_value(self):
        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.json.get_path_json_value("{a,b}"))
        )

        self.assertEqual('SELECT * FROM "abc" WHERE "json"#>\'{a,b}\'', str(q))

    def test_get_path_text_value(self):
        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.json.get_path_text_value("{a,b}"))
        )

        self.assertEqual('SELECT * FROM "abc" WHERE "json"#>>\'{a,b}\'', str(q))


class JSONBOperatorsTests(unittest.TestCase):
    # reference https://www.postgresql.org/docs/9.5/functions-json.html
    table_abc = Table("abc")

    def test_json_contains_for_json(self):
        q = PostgreSQLQuery.select(JSON({"a": 1, "b": 2}).contains({"a": 1}))

        # gotta split this one up to avoid the indeterminate order
        sql = str(q)
        start, end = 9, -13
        self.assertEqual("SELECT '{}'@>'{\"a\":1}'", sql[:start] + sql[end:])

        members_set = set(sql[start:end].split(","))
        self.assertSetEqual({'"a":1', '"b":2'}, members_set)

    def test_json_contains_for_field(self):
        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.json.contains({"dates": "2018-07-10 - 2018-07-17"}))
        )

        self.assertEqual(
            "SELECT * "
            'FROM "abc" '
            'WHERE "json"@>\'{"dates":"2018-07-10 - 2018-07-17"}\'',
            str(q),
        )

    def test_json_contained_by_using_str_arg(self):
        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .select("*")
            .where(
                self.table_abc.json.contained_by(
                    OrderedDict(
                        [("dates", "2018-07-10 - 2018-07-17"), ("imported", "8"),]
                    )
                )
            )
        )
        self.assertEqual(
            'SELECT * FROM "abc" '
            'WHERE "json"<@\'{"dates":"2018-07-10 - 2018-07-17","imported":"8"}\'',
            str(q),
        )

    def test_json_contained_by_using_list_arg(self):
        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.json.contained_by(["One", "Two", "Three"]))
        )

        self.assertEqual(
            'SELECT * FROM "abc" WHERE "json"<@\'["One","Two","Three"]\'', str(q)
        )

    def test_json_contained_by_with_complex_criterion(self):
        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .select("*")
            .where(
                self.table_abc.json.contained_by(["One", "Two", "Three"])
                & (self.table_abc.id == 26)
            )
        )

        self.assertEqual(
            'SELECT * FROM "abc" WHERE "json"<@\'["One","Two","Three"]\' AND "id"=26',
            str(q),
        )

    def test_json_has_key(self):
        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.json.has_key("dates"))
        )

        self.assertEqual('SELECT * FROM "abc" WHERE "json"?\'dates\'', str(q))

    def test_json_has_keys(self):
        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.json.has_keys(["dates", "imported"]))
        )

        self.assertEqual(
            "SELECT * FROM \"abc\" WHERE \"json\"?&ARRAY['dates','imported']", str(q)
        )

    def test_json_has_any_keys(self):
        q = (
            PostgreSQLQuery.from_(self.table_abc)
            .select("*")
            .where(self.table_abc.json.has_any_keys(["dates", "imported"]))
        )

        self.assertEqual(
            "SELECT * FROM \"abc\" WHERE \"json\"?|ARRAY['dates','imported']", str(q)
        )


class DistinctOnTests(unittest.TestCase):
    table_abc = Table("abc")

    def test_distinct_on(self):
        q = PostgreSQLQuery.from_(self.table_abc).distinct_on('lname', self.table_abc.fname).select('lname', 'id')

        self.assertEqual(
            '''SELECT DISTINCT ON("lname","fname") "lname","id" FROM "abc"''', str(q)
        )
