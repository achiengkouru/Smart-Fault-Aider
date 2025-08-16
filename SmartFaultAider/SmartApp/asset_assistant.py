from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Asset
import re

@login_required
def asset_assistant_view(request):
    if 'asset_messages' not in request.session:
        request.session['asset_messages'] = []
    messages = request.session['asset_messages']
    if request.method == 'POST':
        user_input = request.POST.get('user_input', '').strip()
        if user_input:
            messages.append({'sender': 'You', 'text': user_input})
            # Simple asset query logic (expand as needed)
            response = handle_asset_query(user_input)
            messages.append({'sender': 'Asset Assistant', 'text': response})
            request.session['asset_messages'] = messages
    return render(request, 'assets/asset_assistant.html', {'messages': messages})

def handle_asset_query(user_input):
    import difflib
    import logging
    import re
    logger = logging.getLogger(__name__)
    text = user_input.lower().strip()
    # Synonyms for categories
    category_synonyms = {
        'pc': 'PC',
        'computer': 'PC',
        'computers': 'PC',
        'laptop': 'PC',
        'notebook': 'PC',
        'desktop': 'PC',
        'ups': 'UPS',
        'uninterruptible power supply': 'UPS',
        'hp': 'hp',
        'hewlett packard': 'hp',
        # Add more synonyms as needed
    }
    # Synonyms for departments
    department_synonyms = {
        'school': 'EASA',  # Add more mappings as needed
        'easa': 'EASA',
    }
    # Synonyms for status
    status_synonyms = {
        'working': 'WORKING',
        'faulty': 'FAULTY',
        'under repair': 'UNDER_REPAIR',
        'retired': 'RETIRED',
    }
    # Try to extract category, department, and status flexibly
    categories = [cat.strip() for cat in Asset.objects.values_list('category', flat=True).distinct()]
    departments = [dept.strip() for dept in Asset.objects.values_list('department', flat=True).distinct()]
    statuses = [status.strip() for status in Asset.objects.values_list('status', flat=True).distinct()]
    found_category = None
    found_department = None
    found_status = None
    # Check category synonyms first
    for syn, real_cat in category_synonyms.items():
        if syn in text:
            found_category = real_cat
            logger.debug(f"Matched category synonym: {syn} -> {real_cat}")
            break
    # Category matching
    if not found_category:
        for cat in categories:
            if cat.lower() in text:
                found_category = cat
                logger.debug(f"Matched category from categories list: {cat}")
                break
    if not found_category:
        found_category_matches = difflib.get_close_matches(text, categories, n=1, cutoff=0.7)
        if found_category_matches:
            found_category = found_category_matches[0]
            logger.debug(f"Matched category by close match: {found_category}")
    # Department matching with regex for exact match
    for dept in departments:
        pattern = r'\\b' + re.escape(dept.lower()) + r'\\b'
        if re.search(pattern, text):
            found_department = dept
            logger.debug(f"Matched department by regex exact match: {dept}")
            break
    # Department matching (with synonyms)
    if not found_department:
        for syn, real in department_synonyms.items():
            if syn in text:
                found_department = real
                logger.debug(f"Matched department synonym: {syn} -> {real}")
                break
    if not found_department:
        found_department_matches = difflib.get_close_matches(text, departments, n=1, cutoff=0.7)
        if found_department_matches:
            found_department = found_department_matches[0]
            logger.debug(f"Matched department by close match: {found_department}")
    # Status matching (with synonyms)
    for syn, real_status in status_synonyms.items():
        if syn in text:
            found_status = real_status
            logger.debug(f"Matched status synonym: {syn} -> {real_status}")
            break
    if not found_status:
        found_status_matches = difflib.get_close_matches(text, statuses, n=1, cutoff=0.7)
        if found_status_matches:
            found_status = found_status_matches[0]
            logger.debug(f"Matched status by close match: {found_status}")
    # If both found, answer count with status filter
    if found_category and found_department and found_status:
        count = Asset.objects.filter(category__iexact=found_category.strip(), department__iexact=found_department.strip(), status__iexact=found_status.strip()).count()
        logger.debug(f"Count for category '{found_category}', department '{found_department}', and status '{found_status}': {count}")
        return f"There are {count} {found_category}(s) in {found_department} with status {found_status}."
    # If category and department found, answer count
    if found_category and found_department:
        count = Asset.objects.filter(category__iexact=found_category.strip(), department__iexact=found_department.strip()).count()
        logger.debug(f"Count for category '{found_category}' and department '{found_department}': {count}")
        return f"There are {count} {found_category}(s) in {found_department}."
    # If only category, answer total count
    if found_category:
        count = Asset.objects.filter(category__iexact=found_category.strip()).count()
        logger.debug(f"Count for category '{found_category}': {count}")
        return f"There are {count} {found_category}(s) in the school."
    # If only department, list assets in that department
    if found_department:
        assets = Asset.objects.filter(department__iexact=found_department.strip())
        if assets.exists():
            asset_list = ', '.join([a.name for a in assets])
            logger.debug(f"Assets in department '{found_department}': {asset_list}")
            return f"Assets in {found_department}: {asset_list}"
        else:
            logger.debug(f"No assets found in department '{found_department}'")
            return f"No assets found in {found_department}."
    # Try to match common question forms
    if 'how many' in text or 'number of' in text:
        return "Please specify the asset category and/or location. For example: 'How many computers are in EASA?'"
    return "Sorry, I can only answer questions about the school assets right now. Try asking about asset counts or locations!"
