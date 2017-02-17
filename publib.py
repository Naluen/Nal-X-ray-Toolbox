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


def render(template_path, context):
    import jinja2
    import os
    path, filename = os.path.split(template_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(
            path or './')).get_template(filename).render(context)


def data_base_directory():
    import os
    if os.name is 'nt':
        db_directory = r"C:\Users\ang\Dropbox\Experimental_Data"
    else:
        db_directory = r"/Users/zhouang/Dropbox/Experimental_Data"
    return db_directory