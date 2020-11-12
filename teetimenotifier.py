from models import *
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime
import os


def open_sheet():
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    gc = gspread.authorize(credentials)
    link = 'https://docs.google.com/spreadsheets/d/1R3BmywhR5hkjQIam-IIcsdY9j_wMaKKgS61qZ05qJAw/edit?usp=sharing'
    sh = gc.open_by_url(link).sheet1
    return sh


def get_days_desired(bools):
    day_options = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    days = []
    for i in range(len(bools)):
        if bools[i] == 'Yes':
            days.append(day_options[i])

    return days


def create_courses(sheet):
    courses = []
    active_row = sheet.col_values(2)
    active = [x + 1 for x in range(len(active_row)) if active_row[x] == 'Yes']
    for i in active:
        data = sheet.batch_get(['A' + str(i) + ':T' + str(i)])[0][0]
        if data[3] == 'EzLinks':
            courses.append(EzGolf(i, data[0], data[2], get_days_desired(data[10:17]), data[4], data[5], data[6], data[7], data[17], data[19]))
        elif data[3] == 'Quick18':
            courses.append(Quick18(i, data[0], data[2], get_days_desired(data[10:17]), data[4], data[5], data[6], data[7], data[17], data[19]))
        elif data[3] == 'ForeUp':
            courses.append(ForeUp(i, data[0], get_days_desired(data[10:17]), data[4], data[6], data[8], data[9], data[17], data[19], data[2]))

    return courses


def update_previous_found(sheet, courses):
    updates = []
    for course in courses:
        updates.append({'range': 'R' + str(course.row) + ':S' + str(course.row),
                        'values': [[course.extract_ids(), datetime.now(SF).strftime("%m/%d/%Y, %H:%M:%S")]]})
    sheet.batch_update(updates)


def update_html(courses, all_html):
    courses_html = ''
    for course in courses:
        if len(course.html) > 0:
            courses_html += course.html
    if len(courses_html) > 0:
        new_html = all_html.replace('{% block button %} {% endblock %}', courses_html)
        return new_html
    else:
        return None

def send_notifications(html):
    if html is not None:
        Email(os.environ['TOADDR'], 'Tee Times', html)
        SNSTextMessage()


def main():
    # from teetimenotifier import *
    email_html = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional //EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office"><head><style type="text/css">body {margin: 0;padding: 0;}table,td,tr {vertical-align: top;border-collapse: collapse;}* {line-height: inherit;}a[x-apple-data-detectors=true] {color: inherit !important;text-decoration: none !important;} .reservation{ flex-grow: 1; width: 31%; background-color: antiquewhite; border: 1px solid #eee; border-radius: 30px; max-width: 250px; margin: 1%; } .reservation ul{ list-style: none; padding-inline-start: 0; color: #555555; } .course{ display: flex; flex-wrap: wrap; border-top: 2px solid #eee; border-bottom: 2px solid #eee; padding: 10px; } .reserve_btn { background-color: #3AB37C; border-radius: 30px; max-width: 150px; min-height: 30px; border: 3px solid #555; padding-top: 11px; text-transform: uppercase; color: antiquewhite; font-weight: bolder; font-family: sans-serif;} .day{ font-family: sans-serif; font-size: 18px; color: cornflowerblue; text-align: initial; }</style><style type="text/css" id="media-query">@media (max-width: 660px) {.block-grid,.col {min-width: 320px !important;max-width: 100% !important;display: block !important;}.block-grid {width: 100% !important;}.col {width: 100% !important;}.col>div {margin: 0 auto;}img.fullwidth,img.fullwidthOnMobile {max-width: 100% !important;}.no-stack .col {min-width: 0 !important;display: table-cell !important;}.no-stack.two-up .col {width: 50% !important;}.no-stack .col.num4 {width: 33% !important;}.no-stack .col.num8 {width: 66% !important;}.no-stack .col.num4 {width: 33% !important;}.no-stack .col.num3 {width: 25% !important;}.no-stack .col.num6 {width: 50% !important;}.no-stack .col.num9 {width: 75% !important;}.video-block {max-width: none !important;}.mobile_hide {min-height: 0px;max-height: 0px;max-width: 0px;display: none;overflow: hidden;font-size: 0px;}.desktop_hide {display: block !important;max-height: none !important;}}</style></head><body class="clean-body" style="margin: 0; padding: 0; -webkit-text-size-adjust: 100%; background-color: #f8f8f9;"> <div style="background-color:#FEBF10;"> <div class="block-grid " style="Margin: 0 auto; min-width: 320px; max-width: 640px; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word; background-color: #FEBF10;"> <div style="border-collapse: collapse;display: table;width: 100%;background-color:#FEBF10;"> <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#FEBF10;"><tr><td align="center"><table cellpadding="0" cellspacing="0" border="0" style="width:640px"><tr class="layout-full-width" style="background-color:#FEBF10"> <td align="center" width="640" style="background-color:#FEBF10;width:640px; border-top: 0px solid transparent; border-left: 0px solid transparent; border-bottom: 0px solid transparent; border-right: 0px solid transparent;" valign="top"><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding-right: 0px; padding-left: 0px; padding-top:0px; padding-bottom:0px;"> <div class="col num12" style="min-width: 320px; max-width: 640px; display: table-cell; vertical-align: top; width: 640px;"> <div style="width:100% !important;"> <div style="border-top:0px solid transparent; border-left:0px solid transparent; border-bottom:0px solid transparent; border-right:0px solid transparent; padding-top:0px; padding-bottom:0px; padding-right: 0px; padding-left: 0px;"> <table class="divider" border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; vertical-align: top; border-spacing: 0; border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; min-width: 100%; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;" role="presentation" valign="top"> <tbody> <tr style="vertical-align: top;" valign="top"> <td class="divider_inner" style="word-break: break-word; vertical-align: top; min-width: 100%; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%; padding-top: 0px; padding-right: 0px; padding-bottom: 0px; padding-left: 0px;" valign="top"> <table class="divider_content" border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; vertical-align: top; border-spacing: 0; border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-top: 4px solid #FEBF10; width: 100%;" align="center" role="presentation" valign="top"> <tbody> <tr style="vertical-align: top;" valign="top"> <td style="word-break: break-word; vertical-align: top; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;" valign="top"><span></span></td> </tr> </tbody> </table> </td> </tr> </tbody> </table> </div> </div> </div> </td></tr></table> </td></tr></table></td></tr></table> </div> </div> </div> <div style="background-color:transparent; max-height: 30px"> <div class="block-grid " style="Margin: 0 auto; min-width: 320px; max-width: 640px; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word; background-color: #f8f8f9;"> <div style="border-collapse: collapse;display: table;width: 100%;background-color:#f8f8f9;"> <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:transparent;"><tr><td align="center"><table cellpadding="0" cellspacing="0" border="0" style="width:640px"><tr class="layout-full-width" style="background-color:#f8f8f9"> <td align="center" width="640" style="background-color:#f8f8f9;width:640px; border-top: 0px solid transparent; border-left: 0px solid transparent; border-bottom: 0px solid transparent; border-right: 0px solid transparent;" valign="top"><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding-right: 0px; padding-left: 0px; padding-top:5px; padding-bottom:5px;"> <div class="col num12" style="min-width: 320px; max-width: 640px; display: table-cell; vertical-align: top; width: 640px;"> <div style="width:100% !important;"> <!--[if (!mso)&(!IE)]><!--> <div style="border-top:0px solid transparent; border-left:0px solid transparent; border-bottom:0px solid transparent; border-right:0px solid transparent; padding-top:5px; padding-bottom:5px; padding-right: 0px; padding-left: 0px;"> <!--<![endif]--> <table class="divider" border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; vertical-align: top; border-spacing: 0; border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; min-width: 100%; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;" role="presentation" valign="top"> <tbody> <tr style="vertical-align: top;" valign="top"> <td class="divider_inner" style="word-break: break-word; vertical-align: top; min-width: 100%; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%; padding-top: 20px; padding-right: 20px; padding-bottom: 20px; padding-left: 20px;" valign="top"> <table class="divider_content" border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; vertical-align: top; border-spacing: 0; border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-top: 0px solid #BBBBBB; width: 100%;" align="center" role="presentation" valign="top"> <tbody> <tr style="vertical-align: top;" valign="top"> <td style="word-break: break-word; vertical-align: top; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;" valign="top"><span></span></td> </tr> </tbody> </table> </td> </tr> </tbody> </table> <!--[if (!mso)&(!IE)]><!--> </div> <!--<![endif]--> </div> </div> </td></tr></table> </td></tr></table></td></tr></table> </div> </div> </div> <div style="background-color:transparent;"> <div class="block-grid" style="Margin: 0 auto; min-width: 320px; max-width: 640px; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word; background-color: #fff;"> <div style="border-collapse: collapse;display: table;width: 100%;background-color:#fff;"> <div style="border-top:0px solid transparent; border-left:0px solid transparent; border-bottom:0px solid transparent; border-right:0px solid transparent; padding-top:0px; padding-bottom:0px; padding-right: 0px; padding-left: 0px;"> <div class="block-grid " style="Margin: 0 auto; min-width: 320px; max-width: 640px; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word; background-color: #fff;"> <div style="border-collapse: collapse;display: table;width: 100%;background-color:#fff;"> <div style="padding-right: 0px;padding-left: 0px;" align="center"> <div style="font-size:1px;line-height:22px">&nbsp;</div> <img class="center fixedwidth" align="center" border="0" src="https://teetimenotifier.s3-us-west-1.amazonaws.com/teetimenotifier.png" alt="TEETIME" title="TEETIME" style="text-decoration: none; -ms-interpolation-mode: bicubic; border: 0; height: auto; width: 100%; max-width: 128px; display: block;" width="128"> </div> </div> </div> <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding-right: 40px; padding-left: 40px; padding-top: 10px; padding-bottom: 10px; font-family: Tahoma, sans-serif"> <div style="color:#555555;font-family:Montserrat, Trebuchet MS, Lucida Grande, Lucida Sans Unicode, Lucida Sans, Tahoma, sans-serif;line-height:1.2;padding-top:10px;padding-right:40px;padding-bottom:10px;padding-left:40px;"> <div id="title" style="text-align:center; line-height: 1.2; font-size: 30px; color: #555555; font-family: Montserrat, Trebuchet MS, Lucida Grande, Lucida Sans Unicode, Lucida Sans, Tahoma, sans-serif; mso-line-height-alt: 36px;"> Bay Area Tee-Time Notifier </div> </div> </td></tr></table> <table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding-right: 40px; padding-left: 40px; padding-top: 10px; padding-bottom: 10px; font-family: Tahoma, sans-serif"> <div style="color:#555555;font-family:Montserrat, Trebuchet MS, Lucida Grande, Lucida Sans Unicode, Lucida Sans, Tahoma, sans-serif;line-height:1.5;padding-top:10px;padding-right:40px;padding-bottom:10px;padding-left:40px;"> <div id="email_content" style="line-height: 1.5; font-size: 14px; font-family: Montserrat, Trebuchet MS, Lucida Grande, Lucida Sans Unicode, Lucida Sans, Tahoma, sans-serif; color: #555555; mso-line-height-alt: 18px;"> Hey Chris, Here are the available upcoming tee times: </div> </div> </td></tr></table> </div> </div> </div> </div> <div style="background-color:transparent;"> <div class="block-grid " style="Margin: 0 auto; min-width: 320px; max-width: 640px; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word; background-color: #fff;"> <div style="border-collapse: collapse;display: table;width: 100%;background-color:#fff;"> <div style="border-top:0px solid transparent; border-left:0px solid transparent; border-bottom:0px solid transparent; border-right:0px solid transparent; padding-top:0px; padding-bottom:0px; padding-right: 0px; padding-left: 0px;"> <div id="button" class="button-container" align="center" style="padding-top:40px;padding-right:10px;padding-bottom:0px;padding-left:10px;"> {% block button %} {% endblock %} </div> <table class="divider" border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; vertical-align: top; border-spacing: 0; border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; min-width: 100%; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;" role="presentation" valign="top"> <tbody> <tr style="vertical-align: top;" valign="top"> <td class="divider_inner" style="word-break: break-word; vertical-align: top; min-width: 100%; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%; padding-top: 60px; padding-right: 0px; padding-bottom: 12px; padding-left: 0px;" valign="top"> <table class="divider_content" border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; vertical-align: top; border-spacing: 0; border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-top: 0px solid #BBBBBB; width: 100%;" align="center" role="presentation" valign="top"> <tbody> <tr style="vertical-align: top;" valign="top"> <td style="word-break: break-word; vertical-align: top; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;" valign="top"><span></span></td> </tr> </tbody> </table> </td> </tr> </tbody> </table> </div> </div> </div> </div> <div style="background-color:transparent; max-height: 30px"> <div class="block-grid " style="Margin: 0 auto; min-width: 320px; max-width: 640px; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word; background-color: #f8f8f9;"> <div style="border-collapse: collapse;display: table;width: 100%;background-color:#f8f8f9;"> <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:transparent;"><tbody><tr><td align="center"><table cellpadding="0" cellspacing="0" border="0" style="width:640px"><tbody><tr class="layout-full-width" style="background-color:#f8f8f9"> <td align="center" width="640" style="background-color:#f8f8f9;width:640px; border-top: 0px solid transparent; border-left: 0px solid transparent; border-bottom: 0px solid transparent; border-right: 0px solid transparent;" valign="top"><table width="100%" cellpadding="0" cellspacing="0" border="0"><tbody><tr><td style="padding-right: 0px; padding-left: 0px; padding-top:5px; padding-bottom:5px;"> <div class="col num12" style="min-width: 320px; max-width: 640px; display: table-cell; vertical-align: top; width: 640px;"> <div style="width:100% !important;"> <!--[if (!mso)&(!IE)]><!--> <div style="border-top:0px solid transparent; border-left:0px solid transparent; border-bottom:0px solid transparent; border-right:0px solid transparent; padding-top:5px; padding-bottom:5px; padding-right: 0px; padding-left: 0px;"> <!--<![endif]--> <table class="divider" border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; vertical-align: top; border-spacing: 0; border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; min-width: 100%; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;" role="presentation" valign="top"> <tbody> <tr style="vertical-align: top;" valign="top"> <td class="divider_inner" style="word-break: break-word; vertical-align: top; min-width: 100%; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%; padding-top: 20px; padding-right: 20px; padding-bottom: 20px; padding-left: 20px;" valign="top"> <table class="divider_content" border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; vertical-align: top; border-spacing: 0; border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-top: 0px solid #BBBBBB; width: 100%;" align="center" role="presentation" valign="top"> <tbody> <tr style="vertical-align: top;" valign="top"> <td style="word-break: break-word; vertical-align: top; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;" valign="top"><span></span></td> </tr> </tbody> </table> </td> </tr> </tbody> </table> <!--[if (!mso)&(!IE)]><!--> </div> <!--<![endif]--> </div> </div> </td></tr></tbody></table> </td></tr></tbody></table></td></tr></tbody></table> </div> </div> </div> <div style="background-color:transparent;"> <div class="block-grid " style="Margin: 0 auto; min-width: 320px; max-width: 640px; overflow-wrap: break-word; word-wrap: break-word; word-break: break-word; background-color: #3AB37C;"> <div style="border-collapse: collapse;display: table;width: 100%;background-color:#3AB37C;"> <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:transparent;"><tr><td align="center"><table cellpadding="0" cellspacing="0" border="0" style="width:640px"><tr class="layout-full-width" style="background-color:#3AB37C"> <td align="center" width="640" style="background-color:#3AB37C;width:640px; border-top: 0px solid transparent; border-left: 0px solid transparent; border-bottom: 0px solid transparent; border-right: 0px solid transparent;" valign="top"><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding-right: 0px; padding-left: 0px; padding-top:0px; padding-bottom:0px;"> <div class="col num12" style="min-width: 320px; max-width: 640px; display: table-cell; vertical-align: top; width: 640px;"> <div style="width:100% !important;"> <!--[if (!mso)&(!IE)]><!--> <div style="border-top:0px solid transparent; border-left:0px solid transparent; border-bottom:0px solid transparent; border-right:0px solid transparent; padding-top:0px; padding-bottom:0px; padding-right: 0px; padding-left: 0px;"> <!--<![endif]--> <table class="divider" border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; vertical-align: top; border-spacing: 0; border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; min-width: 100%; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;" role="presentation" valign="top"> <tbody> <tr style="vertical-align: top;" valign="top"> <td class="divider_inner" style="word-break: break-word; vertical-align: top; min-width: 100%; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%; padding-top: 0px; padding-right: 0px; padding-bottom: 0px; padding-left: 0px;" valign="top"> <table class="divider_content" border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; vertical-align: top; border-spacing: 0; border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-top: 4px solid #FEBF10; width: 100%;" align="center" role="presentation" valign="top"> <tbody> <tr style="vertical-align: top;" valign="top"> <td style="word-break: break-word; vertical-align: top; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;" valign="top"><span></span></td> </tr> </tbody> </table> </td> </tr> </tbody> </table> <table class="social_icons" cellpadding="0" cellspacing="0" width="100%" role="presentation" style="table-layout: fixed; vertical-align: top; border-spacing: 0; border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt;" valign="top"> <tbody> <tr style="vertical-align: top;" valign="top"> <td style="word-break: break-word; vertical-align: top; padding-top: 28px; padding-right: 10px; padding-bottom: 10px; padding-left: 10px;" valign="top"> <table class="social_table" align="center" cellpadding="0" cellspacing="0" role="presentation" style="table-layout: fixed; vertical-align: top; border-spacing: 0; border-collapse: collapse; mso-table-tspace: 0; mso-table-rspace: 0; mso-table-bspace: 0; mso-table-lspace: 0;" valign="top"> </table> </td> </tr> </tbody> </table> <!--[if mso]><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding-right: 40px; padding-left: 40px; padding-top: 15px; padding-bottom: 10px; font-family: Tahoma, sans-serif"><![endif]--> <div style="color:#555555;font-family:Montserrat, Trebuchet MS, Lucida Grande, Lucida Sans Unicode, Lucida Sans, Tahoma, sans-serif;line-height:1.5;padding-top:15px;padding-right:40px;padding-bottom:10px;padding-left:40px;"> <div style="line-height: 1.5; font-size: 12px; font-family: Montserrat, Trebuchet MS, Lucida Grande, Lucida Sans Unicode, Lucida Sans, Tahoma, sans-serif; color: #555555; mso-line-height-alt: 18px;"> <p style="font-size: 12px; line-height: 1.5; word-break: break-word; text-align: left; font-family: inherit; mso-line-height-alt: 18px; margin: 0;"><span style="color: #262626; font-size: 12px;">Contact <a href="mailto:devgilad@gmail.com" style="color: #262626">Gilad Spitzer</a> for questions, comments, or concerns.</span></p> <p style="font-size: 12px; line-height: 1.5; word-break: break-word; text-align: left; font-family: inherit; mso-line-height-alt: 18px; margin: 0;"><span style="color: #262626; font-size: 12px;">To modify the google sheet, click <a href="https://docs.google.com/spreadsheets/d/1R3BmywhR5hkjQIam-IIcsdY9j_wMaKKgS61qZ05qJAw/edit?usp=sharing" style="color: #262626">here</a>.</span></p> </div> </div> <!--[if mso]></td></tr></table><![endif]--> <table class="divider" border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; vertical-align: top; border-spacing: 0; border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; min-width: 100%; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;" role="presentation" valign="top"> <tbody> <tr style="vertical-align: top;" valign="top"> <td class="divider_inner" style="word-break: break-word; vertical-align: top; min-width: 100%; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%; padding-top: 25px; padding-right: 40px; padding-bottom: 10px; padding-left: 40px;" valign="top"> <table class="divider_content" border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; vertical-align: top; border-spacing: 0; border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; border-top: 1px solid #555961; width: 100%;" align="center" role="presentation" valign="top"> <tbody> <tr style="vertical-align: top;" valign="top"> <td style="word-break: break-word; vertical-align: top; -ms-text-size-adjust: 100%; -webkit-text-size-adjust: 100%;" valign="top"><span></span></td> </tr> </tbody> </table> </td> </tr> </tbody> </table> <!--[if mso]><table width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding-right: 40px; padding-left: 40px; padding-top: 20px; padding-bottom: 30px; font-family: Tahoma, sans-serif"><![endif]--> <div style="color:#555555;font-family:Montserrat, Trebuchet MS, Lucida Grande, Lucida Sans Unicode, Lucida Sans, Tahoma, sans-serif;line-height:1.2;padding-top:20px;padding-right:40px;padding-bottom:30px;padding-left:40px;"> </div> <!--[if mso]></td></tr></table><![endif]--> <!--[if (!mso)&(!IE)]><!--> </div> <!--<![endif]--> </div> </div> </td></tr></table> </td></tr></table></td></tr></table> </div> </div> </div></body></html>'
    sheet = open_sheet()  # returns object with access to Google Sheet
    courses = create_courses(sheet)  # returns list of objects (courses) with all data
    update_previous_found(sheet, courses)
    email_html = update_html(courses, email_html)
    send_notifications(email_html)


def start(event, context):
    try:
        main()
        return 'Success'
    except:
        SNSError('An error has occurred. Please contact Gilad Spitzer to debug')
        return 'An error has occurred. Please contact Gilad Spitzer to debug'

