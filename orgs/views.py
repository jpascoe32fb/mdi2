from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.db.models import Count, Max, Subquery, OuterRef

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.graphics.shapes import Rect
from collections import Counter
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import datetime
import base64, re
from django.core.files.base import ContentFile

import json
from django.core import serializers

from django.conf import settings
from django.views.static import serve
from pathlib import Path

#from functools import wraps
from django.contrib.auth.decorators import login_required
from .decorators import group_required

from .models import *

"""
To fetch only units available to a specific user
use the command
units = Unit.objects.for_user(request.user)
"""

#ex: units = get_units_for_user(request.user)
def get_units_for_user(user):
    user_groups = user.groups.all()
    return Unit.objects.filter(name_groups__in = user_groups)

#for safely returning instances from a model even if none exist | use model.objects.get for single instances
#ie. if a unit doesn't have any reports yet
#ex: reports = safe_get(Report, unit=unit)
def safe_get(model, **kwargs):
    try:
        return model.objects.filter(**kwargs)
    except model.DoesNotExist:
        return None

def get_unit_tree_data(request):
    """
    This function creates the JSON response to create the JSTree.
    Pulls all UnitName objects and each subsequent part so that duplicated leaf nodes
    are represented under the same leaf (dropdown). It is currently called everytime
    a page is loaded with the tree on it.
    """
    #units = UnitName.objects.all()
    user_groups = request.user.groups.all()
    units = UnitName.objects.filter(groups__in=user_groups)
    unit_data = []
    processed_names = set()
    #processed_functions = set()
    #processed_assets = set()
    #processed_components = set()
    #processed_plant_tags = set()

    for unit in units:
        if unit.name not in processed_names:
            processed_names.add(unit.name)
            name_units = Unit.objects.filter(name=unit)
            function_data = []
            processed_functions = set()
            for name_unit in name_units:
                if name_unit.function == None:
                    continue
                if name_unit.function not in processed_functions:
                    processed_functions.add(name_unit.function)
                    function_units = Unit.objects.filter(name=unit, function=name_unit.function)
                    asset_data = []
                    processed_assets = set()
                    for function_unit in function_units:
                        if function_unit.asset == None:
                            continue
                        if function_unit.asset not in processed_assets:
                            processed_assets.add(function_unit.asset)
                            asset_units = Unit.objects.filter(name=unit, function=name_unit.function, asset=function_unit.asset)
                            component_data = []
                            processed_components = set()
                            for asset_unit in asset_units:
                                if asset_unit.component == None:
                                    continue
                                if asset_unit.component not in processed_components:
                                    processed_components.add(asset_unit.component)
                                    component_units = Unit.objects.filter(name=unit, function=name_unit.function, asset=function_unit.asset, component=asset_unit.component)
                                    plant_tag_data = []
                                    processed_plant_tags = set()
                                    for component_unit in component_units:
                                        if component_unit == None:
                                            continue
                                        if component_unit.plant_tag not in processed_plant_tags:
                                            processed_plant_tags.add(component_unit.plant_tag)
                                            #plant_tag_data.append({'name': component_unit.plant_tag.name, 'text': component_unit.plant_tag.name})
                                    component_data.append({'name': asset_unit.component.name, 'children': plant_tag_data, 'text': asset_unit.component.name, 'faid': asset_unit.component.id, 'uid': asset_unit.id, 'type': "Component"})
                            asset_data.append({'name': function_unit.asset.name, 'children': component_data, 'text': function_unit.asset.name, 'faid': function_unit.asset.id, 'uid': function_unit.id, 'type': "Asset"})#may need to make function_unit.id
                    function_data.append({'name': name_unit.function.name, 'children': asset_data, 'text': name_unit.function.name, 'faid': name_unit.function.id, 'uid': name_unit.id, 'type': "Function"})
            unit_data.append({'name': unit.name, 'children': function_data, 'text': unit.name, 'faid': unit.id, 'uid': unit.id, 'type': "Unit"})    
    #print(unit_data)
    return JsonResponse(unit_data, safe=False)

@login_required
@group_required
def home(request):
    """
    This is the function for the dashboard page.
    """
    #units = Unit.objects.all()
    units = Unit.objects.for_user(request.user)
    tree = []
    reports = Report.objects.all()

    context = {'units':units, 'reports':reports, 'tree':tree}
    return render(request, 'orgs/dashboard.html', context)

def login(request):

    if user_authenticated:
        return redirect('home')
    
    print("In login\n")

    context = {}
    return render(request, 'orgs/login.html', context)

def about(request):
    return render(request, 'orgs/about.html')

def generate_pdf(request, report_ids):
    """
    This is the function that generates pdf reports. It utilizes reportlib and
    matplotlib pyplots. Each page is dynamically generated based off of a varying 
    amount of components placed in the report.
    Page 1: Logo Page
    Page 2: Pie Chart Page
    Page 3: Condition Entry Tables Summary
    Page 4+: Condition Entry Details
    """
    report_ids = report_ids.split(',')
    reports = Report.objects.filter(id__in=report_ids)

    PAGE_WIDTH, PAGE_HEIGHT = letter

    # Create a new PDF object
    response = HttpResponse(content_type='application/pdf')
    fname = str(reports.first())
    response['Content-Disposition'] = 'attachment; filename=' + fname + '.pdf'
    #Might change ^ and get rid of attachment
    
    # Create a canvas object with the response object
    p = canvas.Canvas(response)
    
    #Page 1
    # Add logo to the center of the page
    p.drawImage('./static/img/logo.PNG', x=130, y=550, width=None, height=None)
    p.setFont(psfontname='Helvetica', size=18)
    p.drawString(x=130, y=425, text="Condition Assessment Assignment Report")

    
    #Page 2
    # Add general statistics to the next page
    p.showPage()
    p.setFont(psfontname='Helvetica', size=18)
    p.drawString(x=220, y=760, text="Condition Entry Summary")

    severeties = [report.condition.severityLevel for report in reports]
    severity_counts = Counter(severeties)

    # Create pandas DataFrame from the severity data
    #sev_labels = severity_counts.keys()
    #sev_counts = severity_counts.values()
    df = pd.DataFrame.from_dict(severity_counts, orient='index', columns=['count'])
    df.index.name = 'severity'
    df.reset_index(inplace=True)

    #Calculate the percentage for each severity
    df['percentage'] = df['count'] / df['count'].sum() * 100
    df['percentage'] = df['percentage'].round(2)
    
    #Create Pie chart
    sev_color_codes = {
        'HIGH': (1, 0, 0),
        'LOW': (0, 1, 1),
        'MEDIUM': (1, 1, 0),
        'GOOD': (0, 1, 0),
        'MISSED': (0.5, 0.5, 0.5),
        'MED-HIGH': (1, 0, 1),
    }
    plt.figure(figsize=(6, 6))
    sev_pie_colors = [sev_color_codes[severity] for severity in df['severity']]
    patches, texts, autotexts = plt.pie(df['count'], labels=df['severity'], colors=sev_pie_colors, autopct='%1.1f%%')
    plt.title('Severity Distribution')
    for text in texts:
        text.set_size(12)
        text.set_color('gray')
    for autotext in autotexts:
        autotext.set_size(10)

    #Save the chart
    sev_buffer = BytesIO()
    plt.savefig(sev_buffer, format='png')
    sev_buffer.seek(0)

    #Draw the pie chart
    sev_pie = ImageReader(sev_buffer)
    p.drawImage(sev_pie, x=10, y=450, width=300, height=300)

    #Draw the table
    table_data = [['Severity', 'Count', 'Percent']] + df.values.tolist()
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('WIDTH', (2, 0), (2, -1), 80),
    ]))
    table.wrapOn(p, PAGE_WIDTH, PAGE_HEIGHT)
    table.drawOn(p, x=320, y=650)


    #Page 3
    #Condition Entry Tables Summary
    p.showPage()
    p.setFont(psfontname='Helvetica', size=15)
    p.drawString(x=15, y=805, text="Condition Entry Summary")

    col_widths = [90, 125, 105, 125, 115]
    scale_factor = 1.0
    col_widths_scaled = [width * scale_factor for width in col_widths]
    entry_data = [['Level', 'Unit', 'Function', 'Asset', 'Component']]
    for report in reports:
        row = [report.condition.severityLevel, report.unit.name.name, report.unit.function.name, report.unit.asset.name, report.unit.component.name]
        entry_data.append(row)
    entry_tables = Table(entry_data, colWidths=col_widths_scaled)
    table_style = TableStyle([
    # Set the background color of the header row
    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),

    # Set the font size and alignment of the header row
    ('FONTSIZE', (0, 0), (-1, 0), 14),
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

    # Set the font size of the data rows
    ('FONTSIZE', (0, 1), (-1, -1), 12),

    # Set the alternating background color of the data rows
    ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
    ('BACKGROUND', (0, 1), (-1, -2), colors.white),

    #Grid
    ('GRID', (0,0), (-1, -1), 1, colors.black),

    #Grid Padding
    ('TOPPADDING', (0, 1), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
    ])
    entry_tables.setStyle(table_style)
    entry_tables.wrapOn(p, PAGE_WIDTH, PAGE_HEIGHT)
    entry_tables.wrap(0,0)
    entry_tables.drawOn(p, 10, 760)
    
    #Page 4+ Condition Entry Details
    # Loop through the modal data and add information to the PDF
    # *** May need to limit size of text to put in each ***
    for i, report in enumerate(reports):
        p.showPage()
        #titles
        p.setFont(psfontname='Helvetica', size=14)
        p.drawString(x=45, y=795, text="Condition Entry Details")
        p.drawString(x=330, y=795, text="Severity: " + report.condition.severityLevel)
        p.setFont(psfontname='Helvetica-Bold', size=11)
        p.drawString(x=30, y=650, text="Faults")
        p.drawString(x=30, y=580, text="Comments")
        p.drawString(x=30, y=480, text="Recommendations")
        #Rectangle 1, Fault, Comment, Recommend
        p.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.1)
            #1
        p.rect(x=30, y=675, width=530, height=95, fill=True)
            #Fault
        p.rect(x=30, y=605, width=530, height=40, fill=True)
            #Comment
        p.rect(x=30, y=505, width=530, height=70, fill=True)
            #Recommendation
        p.rect(x=30, y=415, width=530, height=60, fill=True)
        #Rect 1 Text
        p.setFillColor(colors.black)
        p.setFont(psfontname='Helvetica', size=10)
        p.drawString(x=70, y=750, text="Unit:  " + report.unit.name.name)
        p.drawString(x=50, y=735, text="Function:  " + report.unit.function.name)
        p.drawString(x=62, y=720, text="Asset:  " + report.unit.asset.name)
        p.drawString(x=45, y=705, text="Component:  " + report.unit.component.name)
        #p.drawString(x=50, y=690, text="Plant Tag:  None")
        #Fault Text
            #p.drawString(x=31, y=625, text=report.fault)
        text = " "#report.fault_group.all() + " :test test test test test test test test test test"
        if len(text) > 125:
            text = text[:120] + '\n' + text[120:]
            #if len(text) > 250: delete after 250 so it doesn't overrun the box
        t_string = p.beginText(x=31, y=635)
        t_string.setFont("Helvetica", 10)
        t_string.setLeading(14)
        lines = text.split("\n", maxsplit=1)
        for line in lines: # maybe change this to only do 2 lines
            t_string.textLine(line)
        p.drawText(t_string)
        #Comment Text
        text = report.comment #+ " :test test test test test test test test test test test test test test test test test test test test test test test test test"
        if len(text) > 125:
            text = text[:120] + '\n' + text[120:]
            #if len(text) > 250: delete after 250 so it doesn't overrun the box
        t_string = p.beginText(x=31, y=565)
        t_string.setFont("Helvetica", 10)
        t_string.setLeading(17)
        lines = text.split("\n", maxsplit=1)
        for line in lines: # maybe change this to only do 2 lines
            t_string.textLine(line)
        p.drawText(t_string)
        #Recommend Text
        text = report.recommendation #+ " :test test test test test test test test test test test test test test test test test test test test test test test test"
        if len(text) > 125:
            text = text[:120] + '\n' + text[120:]
            #if len(text) > 250: delete after 250 so it doesn't overrun the box
        t_string = p.beginText(x=31, y=465)
        t_string.setFont("Helvetica", 10)
        t_string.setLeading(14)
        lines = text.split("\n", maxsplit=1)
        for line in lines: # maybe change this to only do 2 lines
            t_string.textLine(line)
        p.drawText(t_string)

    
    # Save the PDF and return it as a response
    p.save()
    return response

def detailed_condition(request, report_id):
    """
    This is the function called when a detailed page is loaded. It
    pulls all of the data about the specific report and adds it to the 
    page's context.
    report_id: The specific id of a report called by a button.
    """
    report = Report.objects.get(id=report_id)
    fault_list = report.fault_group.all()

    attachments = Attachment.objects.filter(report_instance=report)
    attachments_list = serializers.serialize('json', attachments)

    context = {'report': report, 'fault_list': fault_list, 'attachments_list': attachments_list}
    return render(request, 'orgs/detailed_condition.html', context)

@login_required
@group_required
def company_view(request, node_id):
    """
    This is the function called when a company page is loaded. It
    pulls all of the data about a specific company and adds it to the
    page's context.
    node_id: The id of the UnitName of the company.
    """
    unit_name = UnitName.objects.get(id=node_id)
    units = Unit.objects.filter(name=unit_name)
    all_reports = Report.objects.filter(unit__name=unit_name)
    open_reports = Report.objects.filter(unit__name=unit_name, condition__closed=False)#.order_by('-condition__entry_date')
    
    recent_reports = []
    distinct_units = units.filter(component__isnull=False).distinct()
    for unit in distinct_units:
        temp_report = Report.objects.filter(unit=unit).order_by('-condition__entry_date').first()
        if temp_report != None:
            recent_reports.append(temp_report)

    write_perms = request.user.groups.filter(name='Write').exists()
    
    context = {'unit_name':unit_name, 'units':units, 'open_reports': open_reports, 'all_reports':all_reports, 
               'recent_reports':recent_reports, 'write_perms':write_perms}
    return render(request, 'orgs/company.html', context)

@login_required
@group_required
def function_view(request, node_id):
    """
    This is the function called when a functionality page is loaded. It
    pulls all of the data about a specific function and adds it to the
    page's context.
    node_id: The id of the specific Function.
    """
    function = Function.objects.get(id=node_id)
    units = Unit.objects.filter(function=function)
    unit = units[0]

    all_reports = Report.objects.filter(unit__in=units)
    open_reports = Report.objects.filter(unit__in=units, condition__closed=False)
    
    recent_reports = []
    recent_reports_ids = ""
    for unit in units:
        #can make only closed by adding filter closed=True/False
        recent_temp = Report.objects.filter(unit=unit).order_by('-condition__entry_date').first()
        if recent_temp != None:
            recent_reports.append(recent_temp)
            #so that there isn't a blank space for generate_pdf's split on , to break
            if recent_reports_ids != "":
                recent_reports_ids += "," + "%d" % recent_temp.id
            else:
                recent_reports_ids += "%d" % recent_temp.id

    write_perms = request.user.groups.filter(name='Write').exists()

    context = {'function': function, 'units':units, 'unit':unit, 'recent_reports_ids':recent_reports_ids,
            'open_reports': open_reports, 'all_reports':all_reports, 'write_perms':write_perms}
    return render(request, 'orgs/function.html', context)

@login_required
@group_required
def asset_view(request, asset_id):   
    """
    This is the function called when a asset page is loaded. It
    pulls all of the data about a specific asset and adds it to the
    page's context.
    node_id: The id of the specific Asset.
    """
    asset = Asset.objects.get(id=asset_id)
    units = Unit.objects.filter(asset=asset)
    unit = units[0]

    all_reports = Report.objects.filter(unit__in=units)
    open_reports = Report.objects.filter(unit__in=units, condition__closed=False)

    recent_reports = []
    recent_reports_ids = ""
    for unit in units:
        #can make only closed by adding filter closed=True/False
        recent_temp = Report.objects.filter(unit=unit).order_by('-condition__entry_date').first()
        if recent_temp != None:
            recent_reports.append(recent_temp)
            #so that there isn't a blank space for generate_pdf's split on , to break
            if recent_reports_ids != "":
                recent_reports_ids += "," + "%d" % recent_temp.id
            else:
                recent_reports_ids += "%d" % recent_temp.id

    write_perms = request.user.groups.filter(name='Write').exists()

    context = {'asset': asset, 'units':units, 'unit':unit,'recent_reports_ids':recent_reports_ids,
               'open_reports': open_reports, 'all_reports':all_reports, 'write_perms':write_perms}
    return render(request, 'orgs/asset.html', context)

def unit(request, node_id):
    """
    This is the function called when a Component page is loaded. It
    pulls all of the data about a specific Component and adds it to the
    page's context. It also has a POST check for if a report is made
    for a specific Component
    node_id: The id of the specific Component/Unit object.
    """
    
    if request.method == 'POST':
        techID = request.POST['technology']
        analystID = request.POST['analysts']
        sevID = request.POST['severity']
        entry = request.POST['entryDate']
        req = request.POST['workReq']
        order = request.POST['workOrder']
        fault = request.POST['faults']
        rec = request.POST['recommendations']
        comm = request.POST['comments']

        if Technology.objects.filter(name=techID).exists():
            tech = Technology.objects.get(name=techID)
        else:
            tech = Technology(name=techID)
            tech.save()
        if Analyst.objects.filter(name=analystID).exists():
            anal = Analyst.objects.get(name=analystID)
        else:
            anal = Analyst(name=analystID)
            anal.save()
        cond = Condition(severityLevel=sevID, technology=tech, analyst=anal, entry_date=entry, work_req=req, work_order=order)
        cond.save()
        unitObj = Unit.objects.get(id=node_id)
        new_report = Report(condition=cond, unit=unitObj, fault=fault, comment=comm, recommendation=rec)
        new_report.save()

        return redirect(reverse('unit', args=[node_id]))

    unit = Unit.objects.get(id=node_id)
    reports = Report.objects.filter(unit=unit)
    #severities = {'GOOD','MISSED','LOW', 'MEDIUM','HIGH','MED-HIGH'}
    #severity = Severity.objects.all()

    pie_data = [report.condition.severityLevel for report in reports]
    pie_data = Counter(pie_data)
    severity_labels = []
    severity_data = []
    for data in pie_data:
        severity_labels.append(data)
        temp = pie_data[data]
        severity_data.append(temp)

    write_perms = request.user.groups.filter(name='Write').exists()

    context = {'unit': unit, 'reports': reports, 'severity_data': severity_data,
                'severity_labels': severity_labels, 'write_perms':write_perms}
    return render(request, 'orgs/unit.html', context)


def create_entry(request, node_id):
    """
    This function is used to populate the create_entry page
    as well as handle the submission of a new condition in a POST
    request. This method is called by specific Components
    node_id: The id of the specific Unit
    """
    if request.method == 'POST':
        techID = request.POST['technology']
        analystID = request.POST['analysts']
        sevID = request.POST['severity']
        entry = request.POST['entryDate']
        collection = request.POST['collectionDate']
        p_faultTable = request.POST['faults']
        rec = request.POST['recommendation']
        comm = request.POST['comment']

        p_faults = json.loads(p_faultTable)

        if Technology.objects.filter(name=techID).exists():
            tech = Technology.objects.get(name=techID)
        else:
            tech = Technology(name=techID)
            tech.save()
        if Analyst.objects.filter(name=analystID).exists():
            anal = Analyst.objects.get(name=analystID)
        else:
            anal = Analyst(name=analystID)
            anal.save()
        p_fault_list = []
        for fault in p_faults:
            if FaultGroup.objects.filter(fault=fault['fault'], fault_group=fault['faultGroup']).exists():
                p_new_fault = FaultGroup.objects.get(fault=fault['fault'], fault_group=fault['faultGroup'])
                p_new_fault.used_amount += 1
                p_fault_list.append(p_new_fault)
                p_new_fault.save()
            else:
                p_new_fault = FaultGroup(fault=fault['fault'], fault_group=fault['faultGroup'], used_amount=0)
                p_new_fault.used_amount += 1
                p_fault_list.append(p_new_fault)
                p_new_fault.save()
        cond = Condition(severityLevel=sevID, technology=tech, analyst=anal, entry_date=entry, data_collection_date=collection)
        cond.save()
        unitObj = Unit.objects.get(id=node_id)
        new_report = Report(condition=cond, unit=unitObj, comment=comm, recommendation=rec)
        
        new_report.save()
        new_report.fault_group.set(p_fault_list)

        attachments = request.FILES.getlist('attachments')
        for attachment in attachments:
            new_attachment = Attachment(file=attachment)
            new_attachment.report_instance = new_report
            new_attachment.save()

        return JsonResponse({"data": ""}, status=200)
    
    faults_list = FaultGroup.objects.all()

    technologies = Technology.objects.all()
    analysts = Analyst.objects.all()
    severities = {'GOOD','MISSED','LOW', 'MEDIUM','HIGH','MED-HIGH'}

    context = {'unit_id':node_id, 'severities':severities, 'analysts': analysts, 'technology': technologies,
                'faults_list':faults_list}    
    return render(request, 'orgs/create_entry.html', context)

def edit_entry(request, report_id):
    """
    This function is used to populate the edit_entry page
    as well as handle the submission of an updated condition in a POST
    request. This method is called by specific Components. It pulls all
    of the previous information about the report so it can be viewed/edited.
    report_id: The id of the specific Report to edit
    """
    if request.method == 'POST':
        techID = request.POST['technology']
        analystID = request.POST['analysts']
        sevID = request.POST['severity']
        entry = request.POST['entryDate']
        collection = request.POST['collectionDate']
        p_faultTable = request.POST['faults']
        rec = request.POST['recommendation']
        comm = request.POST['comment']
        #p_report_id = request.POST['report_id']
        p_closed = request.POST['closed']

        closed = False
        if p_closed == "true":
            closed = True

        p_faults = json.loads(p_faultTable)

        if Technology.objects.filter(name=techID).exists():
            tech = Technology.objects.get(name=techID)
        else:
            tech = Technology(name=techID)
            tech.save()
        if Analyst.objects.filter(name=analystID).exists():
            anal = Analyst.objects.get(name=analystID)
        else:
            anal = Analyst(name=analystID)
            anal.save()
        p_fault_list = []
        for fault in p_faults:
            if FaultGroup.objects.filter(fault=fault['fault'], fault_group=fault['faultGroup']).exists():
                p_fault = FaultGroup.objects.get(fault=fault['fault'], fault_group=fault['faultGroup'])
                if Report.objects.filter(id=report_id, fault_group=p_fault).exists():
                    p_fault.used_amount += 1
                    p_fault.save()
                p_fault_list.append(p_fault)
            else:
                p_new_fault = FaultGroup(fault=fault['fault'], fault_group=fault['faultGroup'], used_amount=0)
                p_new_fault.used_amount += 1
                p_fault_list.append(p_new_fault)
                p_new_fault.save()

        p_report = Report.objects.filter(id=report_id)
        for report in p_report: # this is because .get does not sync threads so have to use filter/for
            condition = Condition.objects.get(id=report.condition.id)
            condition.technology = tech
            condition.severityLevel = sevID
            condition.analyst = anal
            condition.entry_date = entry
            condition.data_collection_date=collection
            condition.closed = closed
            condition.save()

            report.comment = comm
            report.recommendation = rec
            report.save()
            report.fault_group.set(p_fault_list)

        # Attachments
        new_attachments = request.POST.getlist('attachments')
        existing_attachments = Attachment.objects.filter(report_instance=p_report[0])

        for urls in existing_attachments:
            if urls.file not in new_attachments:
                urls.delete()

        new_attachments = request.FILES.getlist('attachments')
        for attachment in new_attachments:
            print("new attachment")
            new_attachment = Attachment(file=attachment)
            new_attachment.report_instance = p_report[0]
            new_attachment.save()

        return JsonResponse({"data": ""}, status=200)

    report = Report.objects.get(id=report_id)
    #print(report)
    technologies = Technology.objects.all()
    analysts = Analyst.objects.all()
    severities = {'GOOD','MISSED','LOW', 'MEDIUM','HIGH','MED-HIGH'}
    faults_list = FaultGroup.objects.all()

    try:
        pre_entry_date = report.condition.entry_date.isoformat()
    except:
        pre_entry_date = None
    try:
        pre_collection_date = report.condition.data_collection_date.isoformat()
    except:
        pre_collection_date = None
    pre_faults_list = report.fault_group

    attachments = Attachment.objects.filter(report_instance=report)
    attachments_list = serializers.serialize('json', attachments)

    context = {'entry_date': pre_entry_date, 'collection_date':pre_collection_date, 'report':report, 'unit_id':report.unit.id, 'severities':severities,
                'analysts': analysts, 'technology': technologies, 'faults_list':faults_list,
                'pre_faults_list':list(pre_faults_list.values()), 'attachments':attachments, 'attachments_list':attachments_list}
    return render(request, 'orgs/edit_entry.html', context)

def continue_entry(request, report_id):
    """
    
    """
    if request.method == "POST":
        techID = request.POST['technology']
        analystID = request.POST['analysts']
        sevID = request.POST['severity']
        entry = request.POST['entryDate']
        collection = request.POST['collectionDate']
        p_faultTable = request.POST['faults']
        rec = request.POST['recommendation']
        comm = request.POST['comment']

        p_faults = json.loads(p_faultTable)

        if Technology.objects.filter(name=techID).exists():
            tech = Technology.objects.get(name=techID)
        else:
            tech = Technology(name=techID)
            tech.save()
        if Analyst.objects.filter(name=analystID).exists():
            anal = Analyst.objects.get(name=analystID)
        else:
            anal = Analyst(name=analystID)
            anal.save()
        p_fault_list = []
        for fault in p_faults:
            if FaultGroup.objects.filter(fault=fault['fault'], fault_group=fault['faultGroup']).exists():
                p_fault = FaultGroup.objects.get(fault=fault['fault'], fault_group=fault['faultGroup'])
                if Report.objects.filter(id=report_id, fault_group=p_fault).exists():
                    p_fault.used_amount += 1
                    p_fault.save()
                p_fault_list.append(p_fault)
            else:
                p_new_fault = FaultGroup(fault=fault['fault'], fault_group=fault['faultGroup'], used_amount=0)
                p_new_fault.used_amount += 1
                p_fault_list.append(p_new_fault)
                p_new_fault.save()

        p_report = Report.objects.filter(id=report_id)
        for report in p_report: # this is because .get does not sync threads so have to use filter/for
            condition = Condition.objects.get(id=report.condition.id)
            condition.technology = tech
            condition.severityLevel = sevID
            condition.analyst = anal
            condition.entry_date = entry
            condition.data_collection_date=collection
            condition.save()

            report.comment = comm
            report.recommendation = rec
            report.save()
            report.fault_group.set(p_fault_list)

        # Attachments
        new_attachments = request.POST.getlist('attachments')
        existing_attachments = Attachment.objects.filter(report_instance=p_report[0])

        for urls in existing_attachments:
            if urls.file not in new_attachments:
                urls.delete()

        new_attachments = request.FILES.getlist('attachments')
        for attachment in new_attachments:
            print("new attachment")
            new_attachment = Attachment(file=attachment)
            new_attachment.report_instance = p_report[0]
            new_attachment.save()

        return JsonResponse({"data": ""}, status=200)

    report = Report.objects.get(id=report_id)
    #print(report)
    technologies = Technology.objects.all()
    analysts = Analyst.objects.all()
    severities = {'GOOD','MISSED','LOW', 'MEDIUM','HIGH','MED-HIGH'}
    faults_list = FaultGroup.objects.all()

    try:
        pre_entry_date = report.condition.entry_date.isoformat()
    except:
        pre_entry_date = None
    try:
        pre_collection_date = report.condition.data_collection_date.isoformat()
    except:
        pre_collection_date = None
    pre_faults_list = report.fault_group

    attachments = Attachment.objects.filter(report_instance=report)
    attachments_list = serializers.serialize('json', attachments)

    context = {'entry_date': pre_entry_date, 'collection_date':pre_collection_date, 'report':report, 'unit_id':report.unit.id, 'severities':severities,
                'analysts': analysts, 'technology': technologies, 'faults_list':faults_list,
                'pre_faults_list':list(pre_faults_list.values()), 'attachments':attachments, 'attachments_list':attachments_list}
    return render(request, 'orgs/continue_entry.html', context)

def rename_node(request, node_id):
    """
    This function is called by the JSTree when the rename context
    menu option is selected. It pulls the previous name of the node
    so that it is autofilled in the input box. The POST method calculates
    the level it is at and finds the specific node to be updated.
    """
    if request.method == 'POST':
        level = request.POST['level']
        newName = request.POST['new_name']
        newDesc = request.POST['new_desc']

        if(level == "1"):
            #Company
            unit = UnitName.objects.get(id=node_id)
            unit.name = newName
            unit.description = newDesc
            unit.save()
        elif (level == "2"):
            #Function
            function = Function.objects.get(id=node_id)
            function.name = newName
            function.description = newDesc
            function.save()
        elif (level == "3"):
            #Asset
            asset = Asset.objects.get(id=node_id)
            asset.name = newName
            asset.description = newDesc
            asset.save()
        elif (level == "4"):
            #Component
            component = Component.objects.get(id=node_id)
            component.name = newName
            component.description = newDesc
            component.save()
        return JsonResponse({"data": ""}, status=200)
    #GET requests
    else:
        level = request.GET['level']
        name = ""
        description = ""
        if(level == "1"):
            #Company
            unit = UnitName.objects.get(id=node_id)
            name = unit.name
            description = unit.description
        elif (level == "2"):
            #Function
            function = Function.objects.get(id=node_id)
            name = function.name
            description = function.description
        elif (level == "3"):
            #Asset
            asset = Asset.objects.get(id=node_id)
            name = asset.name
            description = asset.description
        elif (level == "4"):
            #Component
            component = Component.objects.get(id=node_id)
            name = component.name
            description = component.description
        return JsonResponse({"name": name, "description": description}, status=200)

def create_here_node(request, node_id):
    """
    This function is called by the JSTree when the create_here context
    menu option is selected. It uses the height (level) of the selected node to 
    create another node at the same height. Copies the values higher in the tree
    than the selected node
    node_id: The id of the specific node selected to create a new one at the same height
    """
    if request.method == 'POST':
        level = request.POST['level']
        newName = request.POST['new_name']
        newDesc = request.POST['new_desc']

        if(level == "1"):
            #Company
            new_company = UnitName(name=newName, description=newDesc)
            new_company.save()

            new_unit = Unit(name=new_company)
            new_unit.save()
        elif (level == "2"):
            #Function
            new_function = Function(name=newName, description=newDesc)
            new_function.save()
            unit = Unit.objects.get(id=node_id)

            new_unit = Unit(name=unit.name, function=new_function)
            new_unit.save()
        elif (level == "3"):
            #Asset
            new_asset = Asset(name=newName, description=newDesc)
            new_asset.save()
            unit = Unit.objects.get(id=node_id)

            new_unit = Unit(name=unit.name, function=unit.function, asset=new_asset)
            new_unit.save()
        elif (level == "4"):
            #Component
            new_component = Component(name=newName, description=newDesc)
            new_component.save()
            unit = Unit.objects.get(id=node_id)

            new_unit = Unit(name=unit.name, function=unit.function, asset=unit.asset, component=new_component)
            new_unit.save()
        return JsonResponse({"data": ""}, status=200)

    return JsonResponse({"data": ""}, status=400)

def create_child_node(request, node_id):
    """
    This function is called by the JSTree when the create_child context
    menu option is selected. It uses the height (level) of the selected node to 
    create another node at as a leaf. Copies the values higher in the tree
    than the selected node
    node_id: The id of the specific node selected to create a new one at the +1 height
    """
    if request.method == 'POST':
        level = request.POST['level']
        newName = request.POST['new_name']
        newDesc = request.POST['new_desc']

        if(level == "1"):
            #Company -> Function
            new_function = Function(name=newName, description=newDesc)
            new_function.save()
            unit_name = UnitName.objects.get(id=node_id)
            unit = Unit.objects.filter(name=unit_name, function=None).first()
            if unit:
                unit.function = new_function
                unit.save()
            else:
                new_unit = Unit(name=unit_name, function=new_function)
                new_unit.save()
        elif (level == "2"):
            #Function -> Asset
            new_asset = Asset(name=newName, description=newDesc)
            new_asset.save()
            unit = Unit.objects.get(id=node_id)
            if unit.asset == None:
                unit.asset = new_asset
                unit.save()
            else:
                new_unit = Unit(name=unit.name, function=unit.function, asset=new_asset)
                new_unit.save()
        elif (level == "3"):
            #Asset -> Component
            new_component = Component(name=newName, description=newDesc)
            new_component.save()
            unit = Unit.objects.get(id=node_id)
            if unit.component == None:
                unit.component = new_component
                unit.save()
            else:
                new_unit = Unit(name=unit.name, function=unit.function, asset=unit.asset, component=new_component)
                new_unit.save()
        return JsonResponse({"data": ""}, status=200)

    return JsonResponse({"data": ""}, status=400)

def tree_create_copy(request, node_id):
    """
    This function is called by the JSTree when the create_copy context
    menu option is selected. It creates a copy of the selected node with
    the same higher values but not the same children. Both the name and
    description are copied.
    node_id: The specific id of the node to copy
    """
    if request.method == 'POST':
        level = request.POST['level']
        unit = Unit.objects.get(id=node_id)

        if(level == "2"):
            copyF = Function(name=unit.function.name, description=unit.function.description)
            copyF.save()

            copy = Unit(name=unit.name, function=copyF)
            copy.save()
        elif(level == "3"):
            copyA = Asset(name=unit.asset.name, description=unit.asset.description)
            copyA.save()

            copy = Unit(name=unit.name, function=unit.function, asset=copyA)
            copy.save()
        elif(level == "4"):
            copyC = Component(name=unit.component.name, description=unit.component.description)
            copyC.save()

            copy = Unit(name=unit.name, function=unit.function, asset=unit.asset, component=copyC)
            copy.save()
        else:
            return JsonResponse({"data": ""}, status=400)
        return JsonResponse({"data": ""}, status=200)

    return JsonResponse({"data": ""}, status=400)

def show_attachments(request, attachment_url):
    """
    Serves the attachments when loaded by edit_entry, continue_entry, etc. 
    Finds the attachments through the media root + the attachment_url.
    """
    # Attachments stored in 'uploads'
    document_root = str(settings.MEDIA_ROOT)
    return serve(request, attachment_url, document_root=document_root)

def remove_node(request, node_id):
    """
    This function is called by the JSTree when the remove context
    menu option is selected. The POST method calculates the height of the node and
    sets the values at the node and below it to None (so that the values are still stored
    in the database in case of mistakes)
    """
    if request.method == 'POST':
        unit = Unit.objects.get(id=node_id)
        level = request.POST['level']

        if (level == "2"):
            unit_functions = Unit.objects.filter(name=unit.name, function=unit.function)
            for unit in unit_functions:
                unit.function = None
                unit.asset = None
                unit.component = None
                unit.save()
        elif (level == "3"):
            unit_assets = Unit.objects.filter(name=unit.name, function=unit.function, asset=unit.asset)
            for unit in unit_assets:
                unit.asset = None
                unit.component = None
                unit.save()
        elif (level == "4"):
            unit.delete()
        return JsonResponse({"data": ""}, status=200)

    return JsonResponse({"data": ""}, status=400)

def move_node(request):
    """
    This function is called when the JSTree Drag-n-Drop functionality
    is utilized. This function does not ensure if it is a possible move,
    that is done by the tree. It sets the values of the moved node's higher
    values to their new location's parent's higher values.
    """
    if request.method == 'POST':
        type = request.POST['type']
        node_uid = request.POST['node_uid']
        parent_uid = request.POST['parent_uid']

        node = Unit.objects.get(id=node_uid)
        parent = Unit.objects.get(id=parent_uid)

        if type == "Component":
            node.asset = parent.asset
            node.function = parent.function
            node.name = parent.name
            node.save()
        elif type == "Asset":
            children = Unit.objects.filter(name=node.name, function=node.function, asset=node.asset)
            for child in children:
                child.function = parent.function
                child.name = parent.name
                child.save()
            node.function = parent.function
            node.name = parent.name
            node.save()
        elif type == "Function":
            children = Unit.objects.filter(name=node.name, function=node.function)
            for child in children:
                child.name = parent.name
                child.save()
            node.name = parent.name
            node.save()

        return JsonResponse({"data": ""}, status=200)
    return JsonResponse({"data": ""}, status=400)

########################################

def admin_page(request):
    faults = FaultGroup.objects.all()
    technologies = Technology.objects.all()
    analysts = Analyst.objects.all()
    companies = UnitName.objects.all()

    context = {'faults': faults, 'technologies': technologies, 'analysts': analysts, 'companies': companies}
    return render(request, 'orgs/admin.html', context)

### Admin COMPANY functions
def admin_create_company(request):
    if request.method == 'POST':
        company = request.POST['company']

        UnitName(name=company).save()
        return JsonResponse({"data": ""}, status=200)
    return JsonResponse({"data": ""}, status=400)

def admin_edit_company(request, company_id):
    if request.method == 'POST':
        company = request.POST['company']

        old_company = UnitName.objects.get(id=company_id)
        old_company.name = company
        old_company.save()
        return JsonResponse({"data": ""}, status=200)
    else: #GET request
        old_company = UnitName.objects.get(id=company_id)
        return JsonResponse({"old_company_name": old_company.name}, status=200)

def admin_delete_company(request, company_id):
    if request.method == 'POST':
        UnitName.objects.get(id=company_id).delete()
        return JsonResponse({"data": ""}, status=200)
    return JsonResponse({"data": ""}, status=400)

### Admin FAULT functions
def admin_create_fault(request):
    if request.method == 'POST':
        fault = request.POST['fault']
        fault_group = request.POST['fault_group']

        FaultGroup(fault=fault, fault_group=fault_group).save()
        return JsonResponse({"data": ""}, status=200)
    return JsonResponse({"data": ""}, status=400)

def admin_edit_fault(request, fault_id):
    if request.method == 'POST':
        fault = request.POST['fault']
        fault_group = request.POST['fault_group']

        old_fault = FaultGroup.objects.get(id=fault_id)
        old_fault.fault = fault
        old_fault.fault_group = fault_group
        old_fault.save()
        return JsonResponse({"data": ""}, status=200)
    else: #GET request
        old_fault = FaultGroup.objects.get(id=fault_id)
        return JsonResponse({"fault": old_fault.fault, "fault_group": old_fault.fault_group}, status=200)

def admin_delete_fault(request, fault_id):
    if request.method == 'POST':
        fault = FaultGroup.objects.get(id=fault_id)
        fault.delete()
        return JsonResponse({"data": ""}, status=200)
    return JsonResponse({"data": ""}, status=400)

### Admin TECH functions
def admin_create_tech(request):
    if request.method == 'POST':
        tech = request.POST['tech']

        Technology(name=tech).save()
        return JsonResponse({"data": ""}, status=200)
    return JsonResponse({"data": ""}, status=400)

def admin_edit_tech(request, tech_id):
    if request.method == 'POST':
        tech = request.POST['tech']

        old_tech = Technology.objects.get(id=tech_id)
        old_tech.name = tech
        old_tech.save()
        return JsonResponse({"data": ""}, status=200)
    else: #GET request
        old_tech = Technology.objects.get(id=tech_id)
        return JsonResponse({"tech": old_tech.name}, status=200)
    
def admin_delete_tech(request, tech_id):
    if request.method == 'POST':
        tech = Technology.objects.get(id=tech_id)
        tech.delete()
        return JsonResponse({"data": ""}, status=200)
    return JsonResponse({"data": ""}, status=400)

### Admin ANALYST Functions
def admin_create_analyst(request):
    if request.method == 'POST':
        analyst = request.POST['analyst']

        Analyst(name=analyst).save()
        return JsonResponse({"data": ""}, status=200)
    return JsonResponse({"data": ""}, status=400)

def admin_edit_analyst(request, analyst_id):
    if request.method == 'POST':
        analyst = request.POST['analyst']

        old_analyst = Analyst.objects.get(id=analyst_id)
        old_analyst.name = analyst
        old_analyst.save()
        return JsonResponse({"data": ""}, status=200)
    else: #GET request
        old_analyst = Analyst.objects.get(id=analyst_id)
        return JsonResponse({"analyst": old_analyst.name}, status=200)
    
def admin_delete_analyst(request, analyst_id):
    if request.method == 'POST':
        analyst = Analyst.objects.get(id=analyst_id)
        analyst.delete()
        return JsonResponse({"data": ""}, status=200)
    return JsonResponse({"data": ""}, status=400)

######################################

def create_report(request, node_id):
    context = {}
    return render(request, 'orgs/unit.html', context)

def report(request, report_id):
    """
    This function returns a serialized JSON response about a specific report.
    It is currently called when a report is being closed so that the data can be
    ajax called.
    report_id: The specific id of the report to grab
    """
    if request.method == 'GET':
        report = Report.objects.get(id=report_id)
        fault_list = report.fault_group.all()
        serialized_fault_list = serializers.serialize('json', fault_list)
        return JsonResponse({"faults": serialized_fault_list, "tech": report.condition.technology.name, "sevLevel":report.condition.severityLevel,
                            "entryDate": report.condition.entry_date, "comment":report.comment, "recommendation":report.recommendation}, status=200)
    return JsonResponse({"data": ""}, status=400)

def get_table_reports_company(request):
    """
    This function is called for company.html to gather all of the reports
    based of off different filters to be selected on the page.
    """
    if request.method == 'GET':
        type = request.GET['type']
        company = request.GET['company']

        if type == 'openReports':
            reports = Report.objects.filter(unit__name__name=company,condition__closed=False)
            serialized_reports = serializers.serialize('json', reports)
            data = {'reports': serialized_reports}
            return JsonResponse(data, status=200)
        elif type == 'recentReports':
            return JsonResponse({"data": ""}, status=200)
        elif type == 'allReports':
            return JsonResponse({"data": ""}, status=200)

    return JsonResponse({"data": ""}, status=400)

def close_report(request, report_id):
    """
    This function is called when a report is closed. It sets the proper values to 
    closed.
    report_id: The id of the specific report to close
    """
    if request.method == 'POST':
        report = Report.objects.get(id=report_id)
        report.condition.closed = True
        report.condition.close_date = request.POST['closeDate']
        report.condition.reason = request.POST['reason']
        report.condition.save()
        report.save()
        return JsonResponse({"data": ""}, status=200)

    return JsonResponse({"data": ""}, status=400)