# -*- coding: utf-8 -*-
{
    'name': 'Instant Attachment Preview',
    'version': '17.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'mail', 'sale_management'],
    'summary': 'Easily preview PDFs, images, videos, and text files in Odoo records for Res Partner, Sales Orders, and Sales Order Lines.',
    'description': """
        - **Instant File Previews**: Quickly view attachments in a popup without the need for downloading.
        - **Wide File Support**: Preview images (JPEG, PNG, SVG, etc.), videos (MP4, WebM, etc.), PDFs, and text documents.
    """,
    'category': 'Tools',
    'author': " ",
    'website': " ",

    'data': [
        'views/qcent_res_partner_attachment_view.xml',
        'views/qcent_sale_order_attachment_view.xml',
        'views/qcent_sale_order_line_attachment_view.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'instant_attachment_preview/static/src/js/qcent_many2many_attachment_preview.js',
            'instant_attachment_preview/static/src/xml/qcent_many2many_attachment_preview_template.xml',
        ],
    },
    'images': [
        'static/description/assets/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
