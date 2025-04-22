# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Employee Icard',
    'summary': 'Print Standard ID Card for your employee from system',
    'version': '17.0.0.1.0',
    'category': 'extra',
    'author': 'Jupical Technologies Pvt. Ltd.',
    'maintainer': 'Jupical Technologies Pvt. Ltd.',
    'contributors': ['Anil Kesariya <anil.r.kesariya@gmail.com>'],
    'website': 'https://www.jupical.com',
    'depends': ['hr', 'jt_employee_sequence'],
    'data': [

        'reports/emp_classic_back.xml',
        'reports/emp_classic_icard.xml',
        'reports/light_icard_report_front.xml',
        'reports/light_icard_report_back.xml',
        'reports/stylish_icard_report_front.xml',
        'reports/stylish_icard_report_back.xml',
        'reports/green_icard_repot_frontend.xml',
        'reports/green_icard_backend.xml',
        'reports/red_icard_back.xml',
        'reports/purple_icard_frontend.xml',
        'reports/purple_icard_backend.xml',
        'reports/red_icard_front.xml',
        'reports/blue_front_icard.xml',
        'reports/blue_back_icard.xml',
        'reports/square_id_front.xml',
        'reports/square_id_back.xml',
        'reports/white_icard_frontend.xml',
        'reports/white_icard_backend.xml',
        'reports/multi_icard_frontend.xml',
        'reports/multi_icard_backend.xml',
        'reports/navy_icard_frontend.xml',
        'reports/navy_icard_backend.xml',
        'reports/yellow_icard_frontend.xml',
        'reports/yellow_icard_backend.xml',
        'reports/hexagon_icard_frontend.xml',
        'reports/hexagon_icard_backend.xml',
        'view/employee.xml',
    ],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'images': ['static/description/poster_image.gif'],
    'price': 5.00,
    'currency': 'USD'
}
