import os
import re
import glob
import codecs
import logging
import sys
from Poles import PolesFigureFile as PolesFigureFile
import datetime
from recipe_generator import RecipeGenerator
from publib import render as render


def pardic():
    if os.name is 'nt':
        parsdic = r"C:\Users\ang\Dropbox\Experimental_Data"
    else:
        parsdic = r"/Users/zhouang/Dropbox/Experimental_Data"
    return parsdic


def importRSM(context, i, force=0):
    cwd = os.getcwd()
    parsdic = pardic()
    rsmpath = os.path.join(parsdic, 'SSMBE', '%s' % i, 'HR')
    os.chdir(rsmpath)
    direction = ['002', '004', '006', '224']
    img = []
    exception = []
    rsm_num = []
    for k in direction:
        RSM_flag = 1
        if force and os.path.isfile(k + '.raw'):
            rsm.main(k + '.raw')
            if os.path.isfile('%s_%s.png' % (i, k)):
                os.remove('%s_%s.png' % (i, k))
            os.rename('%s.png' % k, '%s_%s.png' % (i, k))
        if not os.path.exists('%s_%s.png' % (i, k)):
            try:
                rsm.main(k + '.raw')
                os.rename('%s.png' % k, '%s_%s.png' % (i, k))
            except FileNotFoundError:
                RSM_flag = 0
                exception.append('%s_%s' % (i, k))
                continue
        if RSM_flag:
            img.append('%s_%s.png' % (i, k))
            rsm_num.append(k)
    if not exception:
        logger.info(exception)
    rsmpath = "/".join(rsmpath.split("\\"))
    img = [(rsmpath + "/" + i) for i in img]
    context['sampledic'][i]['rsm_num'] = rsm_num
    context['sampledic'][i]['img'] = img
    context['sampledic'][i]['RSM'] = RSM_flag

    os.chdir(cwd)
    return context


def search_raw_file(XRDpath):
    raw_file = ''
    raw_file_list = glob.glob('*.raw')
    if len(raw_file_list) == 1:
        raw_file = raw_file_list[0]
    else:
        raw_file = QFileDialog.getOpenFileName(
            #
            caption='Open file',
            directory=XRDpath,
            filter="RAW files (*.raw)"
        )
        raw_file = raw_file[0]
        if not os.path.isfile(raw_file):
            logging.debug('{0}'.format(raw_file))
            raise NameError
    return raw_file


class XRDReportGenerator(PolesFigureFile):
    def __init__(self, sample_name, **generator_preference_dict):
        PolesFigureFile.__init__(self, sample_name)
        self.generator_preference_dict = generator_preference_dict

    def print_result_tex(self):
        """Input the XRD Poles-Figure into the TeX file."""
        parsdic = pardic()
        cwd = os.getcwd()
        XRDflag = 1
        XRDpath = os.path.join(parsdic, 'SSMBE', '%s' % i, 'LR')
        if os.path.exists(XRDpath):
            os.chdir(XRDpath)
            if os.path.isfile("pf.raw"):
                raw_file = "pf.raw"
            else:
                raw_file = search_raw_file(XRDpath)

            if self.generator_preference_dict['is_force']:
                self.plot_2d_image()
                figuredePoles.plotPF(raw_file)
            if os.path.isfile('%s_table.tex' % i):
                with open('%s_table.tex' % i, 'r') as fp:
                    context['sampledic'][i]['MT'] = fp.read()

            if not os.path.exists(i + "_2D.png"):
                para = figuredePoles.plot2D(os.path.abspath(raw_file))
            if (
                            (not os.path.exists(i + "_PF.png")) or
                            (not os.path.exists("MT_density_%s.png" % i)) or
                        (not os.path.exists('%s_table.tex' % i))
            ):
                if not os.path.isfile(raw_file):
                    figuredePoles.plotPF(raw_file)

            try:
                intensity = para['inp_intensity']
            except:
                intensity = measurementMTwinsDensity.beam_intensity(XRDpath, i)
            intensity = (
                "{0:.2f} * 8940 = {1:.3E}".format(intensity / 8940, intensity))

            if XRDflag:
                context['sampledic'][i]['intensity'] = intensity
                context['sampledic'][i]['XRD'] = 1
                XRDpath = "/".join(XRDpath.split("\\"))
                context['sampledic'][i]['XRDpath'] = XRDpath + "/"
            else:
                context['sampledic'][i]['XRD'] = 0
        else:
            context['sampledic'][i]['XRD'] = 0

        os.chdir(cwd)

        return context


def AFMrms():
    txtfile = glob.glob('*.txt')
    rms = ''
    counter = 0
    while counter <= (len(txtfile) - 1):
        statics = codecs.open(
            txtfile[counter], 'r', encoding='utf-8', errors='ignore')
        for lines in statics:
            if lines.startswith("Rms (Sq)"):
                rms = lines.split(":")[1]
        counter += 1
    return rms


def importAFM(context, i):
    """Input the AFM figure into the TeX file."""
    parsdic = pardic()
    cwd = os.getcwd()
    AFMpath = os.path.normpath(os.path.join(parsdic, 'AFM', '%s' % i))
    os.chdir(AFMpath)
    AFMpath = "/".join(AFMpath.split("\\"))
    AFMtitle = glob.glob('*.png')
    [os.rename(i, i.replace('_', '-')) for i in AFMtitle]
    AFMtitle = [i.replace('_', '-') for i in AFMtitle]
    rf = [AFMpath + "/" + i for i in AFMtitle]

    context['sampledic'][i]['imageAFM'] = rf
    context['sampledic'][i]['AFMtitle'] = AFMtitle
    context['sampledic'][i]['rms'] = AFMrms()
    context['sampledic'][i]['AFM'] = 1

    os.chdir(cwd)
    return context


class ReportGenerator(object):
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
        self.sample_list = sample_list
        self.report_type_dict = report_type_dict
        self.generator_preference_dict = generator_preference_dict

    def make_report(self):
        """Make a report including the the figs and recipes.

        Returns:
            None

        Raises:
            Unknown
        """
        context = {'sample': self.sample_list, 'sample_dict': {}}

        now = str(datetime.datetime.now().strftime("%Y_%m_%d"))
        report_directory_str = os.path.join(pardic(), 'Report', now)
        if not os.path.exists(report_directory_str):
            os.makedirs(report_directory_str)

        cwd = report_directory_str
        os.chdir(cwd)

        for i in self.sample_list:
            context['sample_dict'][i] = {}

            recipe_temp = RecipeGenerator(i)
            try:
                recipe_data_str = recipe_temp.tex_generator()
            except NameError as e:
                is_recipe_existed = 0
                print(e)
            else:
                context['sample_dict'][i]['recipe_file'] = (recipe_data_str)
                is_recipe_existed = 1
            context['sample_dict'][i]['recipe'] = is_recipe_existed

        report_title = sorted(
            list(
                key for key, value in self.report_type_dict.items() if value
            )
        )

        tex_file_str = (
            "_".join(report_title) +
            r"_Report_of_" +
            "_".join(self.sample_list) + '.tex'
        )
        report_title = (
            '\\&'.join(report_title) +
            r" Report of " +
            " ".join(self.sample_list)
        )
        context['title'] = report_title

        if self.report_type_dict['XRD']:
            for i in self.sample_list:
                context = importXRD(context, i, force)
        if self.report_type_dict['AFM']:
            for i in sample:
                try:
                    context = importAFM(context, i)
                except FileNotFoundError:
                    logger.info(
                        "AFM ammunition of {0} is in short....".format(i))
        if self.report_type_dict['RSM']:
            for i in sample:
                try:
                    context = importRSM(context, i, force)
                except FileNotFoundError:
                    logger.info(
                        "RSM ammunition of {0} is in short....".format(i))

        os.chdir(cwd)
        tex_file_str = os.path.join(
            os.path.dirname(sys.argv[0]), 'templates', 'template.tex')
        tex_print_str = render(tex_file_str, context)
        tex_print_str = re.sub(r'\{ ', '{', tex_print_str)
        tex_print_str = re.sub(r' \}', '}', tex_print_str)

        with open(tex_file_str, 'wb') as f:
            f.write(tex_print_str.encode('utf-8'))

        return os.path.abspath(tex_file_str)
