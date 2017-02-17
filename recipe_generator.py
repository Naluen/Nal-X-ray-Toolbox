import sys
import logging
import os


class DatabaseConnection(object):
    def __init__(self, sample_name):
        self.sample_name = str(sample_name)
        cursor = None

    @staticmethod
    def connect_database():
        import sys
        try:
            import MySQLdb as mdb
        except ImportError:
            import pymysql as mdb
        if sys.platform.startswith('win32'):
            connection = mdb.connect(
                'localhost', 'ang', 'Anti901201', 'testdb'
            )
        elif sys.platform.startswith('darwin'):
            connection = mdb.connect(
                'localhost', 'ang', 'N8[J?H33}c*m{x', 'testdb'
            )
        return connection.cursor()



    @staticmethod
    def format_data(layer):
        method_dict = {'0': 'MEE', '1': 'MBE', '2': ''}
        layer[1] = method_dict[str(layer[1])]
        layer[2] = int(layer[2])
        layer[3] = float(layer[3])
        return layer

    def is_table_exists(self):
        cursor = self.connect_database()
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = '{0}'
            """.format(self.sample_name.replace('\'', '\'\'')))
        if cursor.fetchone()[0] == 1:
            cursor.close()
            return 1
        else:
            cursor.close()
            return 0

    def read_recipe(self):
        """Delete current structure and reconstruct from DB."""
        cursor = self.connect_database()
        if self.is_table_exists():
            cursor.execute("SELECT * FROM %s" % self.sample_name)
            sample_structure = []
            for row in cursor:
                sample_structure.append(self.format_data(list(row)[1:]))
            cursor.close()
        else:
            raise NameError('No Recipe Found for {0}'.format(self.sample_name))

        return sample_structure


class RecipeGenerator(object):
    def __init__(self, sample_name):
        self.sample_name = sample_name

    def read_recipe(self):
        sample_connection = DatabaseConnection(self.sample_name)
        sample_structure = sample_connection.read_recipe()
        logging.debug("sample recipe structure {0}".format(sample_structure))

        return sample_structure

    def tex_generator(self):
        sample_structure = self.read_recipe()
        context = {'layer': [], 'comment': []}
        for i in sample_structure:
            if i[-1] is not None:
                context['comment'].append(
                    "{0}: {1}\\\\".format(i[0], i[-1]) + os.linesep)
            context['layer'].append(
                "&".join(map(str, i[:-2])) + r"\\" + os.linesep)

        template_file_path = os.path.join(
            os.path.dirname(sys.argv[0]), 'templates', 'RecipeTable.tex')
        data = render(template_file_path, context)
        return data


if __name__ == '__main__':
    p = RecipeGenerator("S1970")
    try:
        structure = p.tex_generator()
    except NameError:
        print(1)
    else:
        print(structure)
