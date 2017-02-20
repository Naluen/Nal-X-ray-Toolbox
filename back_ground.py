import abc
import codecs
import datetime
import glob
import logging
import os
import re
import subprocess
import sys

from PyQt5.QtWidgets import QFileDialog as QFileDialog

from Poles import PolesFigureFile as PolesFigureFile


class Generator(object):
    def __init__(self):
        self.context_dict = None

    @staticmethod
    def data_base_directory():
        import os
        if os.name is 'nt':
            db_directory = r"C:\Users\ang\Dropbox\Experimental_Data"
        else:
            db_directory = r"/Users/zhouang/Dropbox/Experimental_Data"
        return db_directory

    @staticmethod
    def render(template_path, context):
        import jinja2
        import os
        path, filename = os.path.split(template_path)
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(
                path or './')).get_template(filename).render(context)

    @abc.abstractclassmethod
    def write_context_dict(self):
        raise NotImplementedError

    def progress_context(self, context_dict):
        self.context_dict = context_dict
        self.write_context_dict()
        return self.context_dict


class DatabaseConnection(object):
    def __init__(self, sample_name):
        self.sample_name = str(sample_name)

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
        else:
            connection = None
            raise ConnectionError
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


class RecipeGenerator(Generator):
    def __init__(self, sample_name):
        super(RecipeGenerator, self).__init__()
        self.sample_name = sample_name
        self.context_dict = {'layer': [], 'comment': []}

    def read_recipe(self):
        sample_connection = DatabaseConnection(self.sample_name)
        sample_structure = sample_connection.read_recipe()
        logging.debug("sample recipe structure {0}".format(sample_structure))

        return sample_structure

    def write_context_dict(self):
        sample_structure = self.read_recipe()
        for i in sample_structure:
            if i[-1] is not None:
                self.context_dict['comment'].append(
                    "{0}: {1}\\\\".format(i[0], i[-1]) + os.linesep)
            self.context_dict['layer'].append(
                "&".join(map(str, i[:-2])) + r"\\" + os.linesep)

    def tex_generator(self):
        self.write_context_dict()
        template_file_path = os.path.join(
            os.path.dirname(sys.argv[0]), 'templates', 'RecipeTable.tex')
        data = self.render(template_file_path, self.context_dict)
        return data


class AFMReportGenerator(Generator):
    def __init__(self, sample_name):
        super(AFMReportGenerator, self).__init__()
        self.sample_name = sample_name

    @staticmethod
    def afm_rms_search():
        text_file = glob.glob('*.txt')
        rms = ''
        counter = 0
        while counter <= (len(text_file) - 1):
            statics = codecs.open(
                text_file[counter], 'r', encoding='utf-8', errors='ignore')
            for lines in statics:
                if lines.startswith("Rms (Sq)"):
                    rms = lines.split(":")[1]
            counter += 1
        return rms

    def write_context_dict(self):
        """Input the AFM figure into the TeX file."""
        db_directory = self.data_base_directory()
        afm_work_path = os.path.normpath(
            os.path.join(db_directory, 'AFM', '%s' % self.sample_name)
        )

        cwd = os.getcwd()
        os.chdir(afm_work_path)

        afm_title = "/".join(afm_work_path.split("\\"))
        png_file_list = glob.glob('*.png')
        [os.rename(i, i.replace('_', '-')) for i in png_file_list]
        png_file_list = [i.replace('_', '-') for i in png_file_list]
        rf = [afm_title + "/" + i for i in png_file_list]

        self.context_dict['sample_dict'][self.sample_name]['imageAFM'] = rf
        self.context_dict['sample_dict'][self.sample_name]['AFMtitle'] = \
            afm_title
        self.context_dict['sample_dict'][self.sample_name]['rms'] = \
            self.afm_rms_search()
        self.context_dict['sample_dict'][self.sample_name]['AFM'] = 1

        os.chdir(cwd)


# class RSMReportGenerator(Generator):
#     def __init__(self, sample_name):
#         super(RSMReportGenerator, self).__init__()
#         self.sample_name = sample_name
#
#     def write_context_dict(self):
#         cwd = os.getcwd()
#
#         db_directory = self.data_base_directory()
#         rsm_work_path = os.path.join(
#             db_directory, 'SSMBE', '%s' % self.sample_name, 'HR'
#         )
#         os.chdir(rsm_work_path)
#
#         direction = ['002', '004', '006', '224']
#         img = []
#         exception = []
#         rsm_num = []
#         for k in direction:
#             RSM_flag = 1
#             if force and os.path.isfile(k + '.raw'):
#                 rsm.main(k + '.raw')
#                 if os.path.isfile('%s_%s.png' % (i, k)):
#                     os.remove('%s_%s.png' % (i, k))
#                 os.rename('%s.png' % k, '%s_%s.png' % (i, k))
#             if not os.path.exists('%s_%s.png' % (i, k)):
#                 try:
#                     rsm.main(k + '.raw')
#                     os.rename('%s.png' % k, '%s_%s.png' % (i, k))
#                 except FileNotFoundError:
#                     RSM_flag = 0
#                     exception.append('%s_%s' % (i, k))
#                     continue
#             if RSM_flag:
#                 img.append('%s_%s.png' % (i, k))
#                 rsm_num.append(k)
#         if not exception:
#             logging.info(exception)
#         rsm_work_path = "/".join(rsm_work_path.split("\\"))
#         img = [(rsm_work_path + "/" + i) for i in img]
#
#         self.context_dict['sample_dict'][self.sample_name]['rsm_num'] = rsm_num
#         self.context_dict['sample_dict'][self.sample_name]['img'] = img
#         self.context_dict['sample_dict'][self.sample_name]['RSM'] = RSM_flag
#
#         os.chdir(cwd)


class XRDReportGenerator(Generator, PolesFigureFile):
    def __init__(self, sample_name, **generator_preference_dict):
        self.cwd = os.getcwd()
        self.sample_name = sample_name

        db_directory = self.data_base_directory()
        xrd_work_path = os.path.join(
            db_directory, 'SSMBE', '%s' % sample_name, 'LR')
        if os.path.exists(xrd_work_path):
            os.chdir(xrd_work_path)
        else:
            raise FileNotFoundError

        if os.path.isfile("pf.raw"):
            raw_file_name = os.path.join(xrd_work_path, "pf.raw")
        else:
            raw_file_name = QFileDialog.getOpenFileName(
                caption='Open file',
                directory=xrd_work_path,
                filter="RAW files (*.raw)"
            )
            raw_file_name = raw_file_name[0]
        PolesFigureFile.__init__(self, raw_file_name)
        Generator.__init__(self)

        self.generator_preference_dict = generator_preference_dict
        self.xrd_work_path = xrd_work_path

    def print_peak_intensity_list_tex(self):
        """

        :return: formatted micro-twins table.
        """
        result = self.plot_2d_measurement(is_save_image=False)
        result = self.mt_intensity_to_fraction(result)

        peak_intensity_list = list(result['peak_intensity_matrix'])
        peak_intensity_list = [round(i, 2) for i in peak_intensity_list]
        intensity_sum = sum(peak_intensity_list)
        peak_intensity_list.append(intensity_sum)
        peak_intensity_list = list(map(str, peak_intensity_list))
        peak_intensity_list.insert(0, "Intensity")

        mt_dict = {
            'MT': (
                "&".join(peak_intensity_list) +
                r"\\" +
                os.linesep
            )
        }
        template_file_path = os.path.join(
            os.path.dirname(sys.argv[0]),
            'templates',
            'mt_table.tex'
        )
        mt_v_fraction_data_str = self.render(
            template_file_path,
            mt_dict
        )
        return mt_v_fraction_data_str

    def write_context_dict(self):
        """Input the XRD Poles-Figure into the TeX file."""

        intensity = self.beam_intensity()
        intensity_str = (
            "{0:.2f} * 8940 = {1:.3E}".format(intensity / 8940, intensity))
        self.context_dict['sample_dict'][self.sample_name]['intensity'] = \
            intensity_str

        if (
                    ('is_force' in self.generator_preference_dict) and
                    self.generator_preference_dict['is_force']
        ):
            self.plot_polar_image()
            self.plot_2d_image()
            self.plot_2d_measurement()
        else:
            if not os.path.exists(self.sample_name + "_2D.png"):
                self.plot_2d_image()
            if not os.path.exists(self.sample_name + "_PF.png"):
                self.plot_polar_image()
            if not os.path.exists('mt_density' + self.sample_name + '.png'):
                self.plot_2d_measurement()

        mt_v_fraction_data_str = self.print_peak_intensity_list_tex()
        self.context_dict['sample_dict'][self.sample_name][
            'MT'] = mt_v_fraction_data_str

        xrd_work_path_str = "/".join(self.xrd_work_path.split("\\"))
        self.context_dict['sample_dict'][self.sample_name]['xrd_path'] = \
            xrd_work_path_str + "/"

        os.chdir(self.cwd)


class ReportGenerator(Generator):
    def __init__(
            self,
            sample_list,
            report_type_dict,
            **generator_preference_dict
    ):
        """
        :param sample_list: The list of sample.
        :param report_type_dict: The report type.
        :param generator_preference_dict: generator preference.
        """
        super(ReportGenerator, self).__init__()
        self.sample_list = sample_list
        self.report_type_dict = report_type_dict
        self.generator_preference_dict = generator_preference_dict

    def write_context_dict(self):
        """Make a report including the the figs and recipes.

        Returns:
            None

        Raises:
            Unknown
        """
        self.context_dict = {'sample': self.sample_list, 'sample_dict': {}}

        now = str(datetime.datetime.now().strftime("%Y_%m_%d"))
        db_directory = self.data_base_directory()
        report_directory_str = os.path.join(db_directory, 'Report', now)
        if not os.path.exists(report_directory_str):
            os.makedirs(report_directory_str)

        cwd = report_directory_str
        os.chdir(cwd)

        for i in self.sample_list:
            self.context_dict['sample_dict'][i] = {}

            recipe_temp = RecipeGenerator(i)
            try:
                recipe_data_str = recipe_temp.tex_generator()
            except (NameError, ConnectionError) as e:
                self.context_dict['sample_dict'][i]['recipe'] = 0
                print(e)
            else:
                self.context_dict['sample_dict'][i]['recipe_file'] = \
                    recipe_data_str
                self.context_dict['sample_dict'][i]['recipe'] = 1

        report_title = sorted(
            list(
                key for key, value in self.report_type_dict.items() if value
            )
        )

        report_title = (
            '\\&'.join(report_title) +
            r" Report of " +
            " ".join(self.sample_list)
        )
        self.context_dict['title'] = report_title

        if self.report_type_dict['xrd']:
            for i in self.sample_list:
                xrd_temp_object = XRDReportGenerator(
                    i, **self.generator_preference_dict
                )
                try:
                    self.context_dict = xrd_temp_object.progress_context(
                        self.context_dict
                    )
                except FileNotFoundError:
                    self.context_dict['sample_dict'][i]['XRD'] = 0
                else:
                    self.context_dict['sample_dict'][i]['XRD'] = 1
        logging.debug(self.context_dict['sample_dict'])
        if self.report_type_dict['afm']:
            for i in self.sample_list:
                afm_temp_object = AFMReportGenerator(i)
                try:
                    self.context_dict = afm_temp_object.progress_context(
                        self.context_dict
                    )
                except FileNotFoundError:
                    logging.info(
                        "AFM ammunition of {0} is in short....".format(i))
                    self.context_dict['sample_dict'][i]['AFM'] = 0
                else:
                    self.context_dict['sample_dict'][i]['AFM'] = 1
        # if self.report_type_dict['rsm']:
        #     for i in self.sample_list:
        #         try:
        #             self.context_dict = importRSM(self.context_dict, i, force)
        #         except FileNotFoundError:
        #             logging.info(
        #                 "RSM ammunition of {0} is in short....".format(i))

        os.chdir(cwd)

    def tex_progress(self):
        """Make pdf from TeX file.

        Args:
            tex_file_str: the TeX File name

        Returns:
            None

        Raises:
            Unknown
        """
        self.write_context_dict()
        tex_template_file_str = os.path.join(
            os.path.dirname(sys.argv[0]), 'templates', 'template.tex')
        tex_print_str = self.render(tex_template_file_str, self.context_dict)
        tex_print_str = re.sub(r'\{ ', '{', tex_print_str)
        tex_print_str = re.sub(r' \}', '}', tex_print_str)

        tex_file_str = "_".join(self.context_dict['title'].split()) + ".tex"

        with open(tex_file_str, 'wb') as f:
            f.write(tex_print_str.encode('utf-8'))

        process = subprocess.Popen(
            'pdflatex --interaction=nonstopmode {0}'.format(tex_file_str),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = process.communicate()
        # if out:
        #     print("standard output of subprocess:")
        #     print(out)
        # if err:
        #     print("standard error of subprocess:")
        #     print(err)
        if (
                    ('is_clear_cache' in self.generator_preference_dict) and
                    self.generator_preference_dict['is_clear_cache']
        ):
            try:
                os.remove(tex_file_str.replace(".tex", ".aux"))
                os.remove(tex_file_str.replace(".tex", ".log"))
            except FileNotFoundError:
                logging.info("Not found log or aux file...")
