# -*- coding: utf-8 -*-
"""English -> Arabic for the two construction modules.

Terminology follows the client's own operations notes: مناقصة for a tender,
مقايسة for the bill of quantities, مستخلص for a payment certificate,
تأمين ابتدائي / نهائي for the bid and performance bonds.
"""

AR = {
    # ---- generic ----
    "Name": "الاسم", "Code": "الكود", "Reference": "المرجع", "Sequence": "الترتيب",
    "Active": "نشط", "Notes": "ملاحظات", "Description": "الوصف", "Details": "التفاصيل",
    "Date": "التاريخ", "Dates": "التواريخ", "Type": "النوع", "Status": "الحالة",
    "Amount": "المبلغ", "Cost": "التكلفة", "Client": "العميل", "Summary": "الملخص",
    "Period": "الفترة", "Reason": "السبب", "Result": "النتيجة", "Revenue": "الإيرادات",
    "Scope": "نطاق العمل", "Subject": "الموضوع", "Taxes": "الضرائب", "UOM": "الوحدة",
    "File": "الملف", "Files": "الملفات", "Document": "مستند", "Documents": "المستندات",
    "Employee": "الموظف", "Employees": "الموظفون", "Team": "الفريق",
    "Settings": "الإعدادات", "Configuration": "الإعدادات", "Dashboard": "لوحة المتابعة",
    "Schedule": "الجدول الزمني", "Checklist": "قائمة المراجعة", "Rating": "التقييم",
    "Resolution": "التسوية", "Responsible": "المسؤول", "Reported By": "أبلغ عنه",
    "Expiry Date": "تاريخ الانتهاء", "Issue Date": "تاريخ الإصدار",
    "Payment Terms": "شروط السداد", "Required": "مطلوب", "Missing": "ناقص",
    "Provided": "مُقدَّم", "Provided On": "تاريخ التقديم", "Expired": "منتهي",
    "Expires": "له تاريخ انتهاء", "Used For": "يُستخدم في", "Both": "الاثنان",
    "Opinion": "الرأي", "Decision": "القرار", "Submission": "التقديم",
    "Instrument": "أداة الضمان", "Validity": "سريان الضمان", "Stores": "المخازن",
    "Live": "جارية", "Running": "جارٍ", "Outstanding": "قائم", "Request": "طلب",
    "New Certificate": "مستخلص جديد", "Certificates": "المستخلصات",

    # ---- actions / buttons ----
    "Activate": "تفعيل", "Cancel": "إلغاء", "Confirm": "تأكيد", "Close": "إغلاق",
    "Complete": "إنهاء", "Reject": "رفض", "Approve": "اعتماد", "Revise": "مراجعة",
    "Reset": "إعادة تعيين", "Reset to Draft": "إرجاع لمسودة", "Reset to Open": "إعادة فتح",
    "Start": "بدء", "Submit": "تقديم", "Terminate": "إنهاء التعاقد", "Hold": "إيقاف",
    "Mark Done": "تعليم كمنتهٍ", "Mark Lost": "تعليم كخسارة", "Mark Paid": "تعليم كمدفوع",
    "Mark Delayed": "تعليم كمتأخر", "Mark Invoiced": "تعليم كمفوتر",
    "Mark Received": "تعليم كمستلم", "Mark Won & Create Project": "ترسية وإنشاء مشروع",
    "Start Preparation": "بدء الدراسة", "Start Inspection": "بدء الفحص",
    "Start Handover": "بدء التسليم", "Submit Bid": "تقديم العطاء",
    "Print BOQ": "طباعة المقايسة", "Create RFQ": "إنشاء طلب عرض سعر",
    "Create/Open PO": "إنشاء/فتح أمر شراء", "Create Invoice / Bill": "إنشاء فاتورة",
    "Open Invoice / Bill": "فتح الفاتورة",
    "Request Approval": "طلب موافقة الإدارة", "Approve Opening": "اعتماد فتح العملية",
    "Reject Tender": "رفض المناقصة", "Hold Project": "إيقاف المشروع",
    "Load Standard Checklist": "تحميل قائمة المستندات القياسية",
    "Re-apply company ratios": "إعادة تطبيق نسب الشركة",
    "Pricing Sheet (Excel)": "جدول التسعير (إكسل)",
    "Register Booklet Fee Payment": "تسجيل صرف ثمن الكراسة",
    "Bond Issued": "تم إصدار التأمين", "Bond Released": "تم رد التأمين",
    "Bond Forfeited": "تم مصادرة التأمين",

    # ---- states ----
    "Draft": "مسودة", "Confirmed": "مؤكد", "In Progress": "قيد التنفيذ",
    "Done": "منتهٍ", "Cancelled": "ملغي", "Completed": "مكتمل", "Approved": "معتمد",
    "Submitted": "مُقدَّم", "Rejected": "مرفوض", "Invoiced": "مفوتر", "Paid": "مدفوع",
    "Received": "مستلم", "Ordered": "تم الطلب", "Planned": "مخطط", "Delayed": "متأخر",
    "On Hold": "موقوف", "Open": "مفتوح", "Closed": "مغلق", "Won": "فائزة",
    "Lost": "خاسرة", "Revised": "مُعدَّل", "Terminated": "منتهي التعاقد",
    "Failed": "فشل", "Fail": "راسب", "Pass": "ناجح", "Conditional Pass": "ناجح بشروط",
    "Handover": "تحت التسليم", "In Handover": "تحت التسليم",
    "Waiting Approval": "بانتظار الموافقة",
    "Waiting Management Approval": "بانتظار موافقة الإدارة",
    "Rejected by Management": "مرفوضة من الإدارة",
    "Lost - Bond Not Released": "خاسرة - التأمين لم يُرد",
    "Preparing Bid": "إعداد العطاء", "RFQ Created": "تم إنشاء طلب عرض السعر",
    "Invoiced/Billed": "مفوتر", "Not Required": "غير مطلوب", "To Issue": "للإصدار",
    "Issued": "صادر", "Held by Client": "محجوز لدى العميل", "Released": "مُرد",
    "Forfeited": "مُصادر",

    # ---- tender ----
    "Tender": "مناقصة", "Tenders": "المناقصات", "Tender / Bid": "مناقصة / عطاء",
    "Tender Details": "بيانات المناقصة", "Tender Item": "بند المناقصة",
    "Tender Items": "بنود المناقصة", "Tender Engineer": "مهندس المناقصة",
    "Tender Files": "ملفات المناقصات", "Tender Name...": "اسم المناقصة...",
    "Tendering Authority / Client": "الجهة المالكة / العميل",
    "Tendering Authority Type": "نوع الجهة المالكة",
    "Authority Type": "نوع الجهة", "Authority Types": "أنواع الجهات",
    "Government Body": "جهة حكومية", "Public": "مناقصة عامة", "Private": "مناقصة محدودة",
    "Negotiated": "أمر مباشر", "Loss Reason": "سبب الخسارة",
    "Awarded Project": "المشروع بعد الترسية", "Originating Tender": "المناقصة الأصلية",
    "Submission Deadline": "موعد التسليم", 
     "Operation Duration (days)": "مدة العملية (أيام)",
    "Declared Operation Value": "القيمة المعلنة للعملية",
    "Conditions Booklet": "كراسة الشروط", "Booklet & Bond": "الكراسة والتأمين",
    "Tender Document Fee": "ثمن كراسة الشروط", "Booklet Purchased": "تم شراء الكراسة",
    "Purchase Date": "تاريخ الشراء", "Fee Payment": "سند صرف الثمن",
    "Estimated Financials": "التقديرات المالية", "Scope & Notes": "نطاق العمل والملاحظات",
    "Scope of work...": "نطاق العمل...", "Internal notes...": "ملاحظات داخلية...",
    "Deadline in 7 Days": "الموعد خلال ٧ أيام",
    "Incomplete Bid File": "ملف عطاء غير مكتمل", "Bid File": "ملف العطاء",
    "Do we bid, and on what terms?": "هل نتقدم للمناقصة، وبأي شروط؟",
    "Why is this operation not worth opening?": "لماذا لا تستحق العملية الفتح؟",

    # ---- approval ----
    "Approval Request": "طلب الفتح", "Approval Date": "تاريخ الاعتماد",
    "Approved By": "اعتمدها", "Rejection Reason": "سبب الرفض",
    "Requested Budget": "المبلغ المطلوب", "Requested Engineers": "المهندسون المطلوبون",
    "Requested from Management": "المطلوب من الإدارة",
    "Reminder Lead Time": "مهلة التذكير", "Remind Before (days)": "التذكير قبل (أيام)",
    "Tender Reminder (days)": "تذكير المناقصات (أيام)",

    # ---- bonds ----
    "Bid Bond": "التأمين الابتدائي", "Bid Bond (%)": "نسبة التأمين الابتدائي (%)",
    "Bid Bond Amount": "قيمة التأمين الابتدائي",
    "Bid Bond Required": "التأمين الابتدائي مطلوب",
    "Bid Bond Ratio (%)": "نسبة التأمين الابتدائي (%)",
    "Default Bid Bond (%)": "نسبة التأمين الابتدائي الافتراضية (%)",
    "Performance Bond": "التأمين النهائي",
    "Performance Bond (%)": "نسبة التأمين النهائي (%)",
    "Performance Bond Amount": "قيمة التأمين النهائي",
    "Performance Bond Required": "التأمين النهائي مطلوب",
    "Performance Bond Ratio (%)": "نسبة التأمين النهائي (%)",
    "Bond Status": "حالة التأمين", "Bond Reference": "رقم خطاب الضمان",
    "Bond Instrument": "نوع الضمان", "Bond Issue Date": "تاريخ إصدار الضمان",
    "Bond Expiry Date": "تاريخ انتهاء الضمان", "Bond Release Date": "تاريخ رد التأمين",
    "Bond Outstanding": "تأمين قائم", "Issuing Bank": "البنك المُصدِر",
    "Cash Deposit": "إيداع نقدي", "Certified Cheque": "شيك مقبول الدفع",
    "Letter of Guarantee": "خطاب ضمان",

    # ---- pricing ----
    "Build-up Pricing": "التسعير التراكمي", "Dry Cost": "تكلفة الخامات",
    "Operating Cost": "تكلفة التشغيل", "Base Cost": "التكلفة الأساسية",
    "Profit": "الربح", "Profit (%)": "نسبة الربح (%)", "Profit Ratio (%)": "نسبة الربح (%)",
    "Contingency": "الطوارئ", "Contingency (%)": "نسبة الطوارئ (%)",
    "Contingency Ratio (%)": "نسبة الطوارئ (%)",
    "Administration": "الإدارة", "Administration (%)": "نسبة الإدارة (%)",
    "Administration Ratio (%)": "نسبة الإدارة (%)",
    "General Expenses": "المصاريف العمومية",
    "General Expenses (%)": "نسبة المصاريف العمومية (%)",
    "General Expenses Ratio (%)": "نسبة المصاريف العمومية (%)",
    "Total Markup (%)": "إجمالي نسبة الإضافة (%)", "Markup Value": "قيمة الإضافة",
    "Price before Expenses": "السعر قبل المصاريف", "Expenses Value": "قيمة المصاريف",
    "Budget Cost Rate": "سعر التكلفة التقديري",

    # ---- BOQ ----
    "BOQ": "المقايسة", "BOQ Item": "بند المقايسة", "BOQ Items": "بنود المقايسة",
    "BOQ Line": "بند المقايسة", "BOQ Lines": "بنود المقايسة",
    "Bill of Quantities": "مقايسة", "Total BOQ Amount": "إجمالي قيمة المقايسة",
    "BOQ / Cost Control": "المقايسة وضبط التكلفة",
    "Quantity Variance": "فرق الكمية", "Variance Cost": "تكلفة الفرق",
    "Over-run": "تجاوز الكمية", "Product / Service": "المنتج / الخدمة",

    # ---- project ----
    "Project": "مشروع", "Projects": "المشاريع", "Construction Project": "مشروع مقاولات",
    "Project Details": "بيانات المشروع", "Project Manager": "مدير المشروع",
    "Site Manager": "مدير الموقع", "Project Name...": "اسم المشروع...",
    "Project File": "ملف المشروع", "Project Files": "ملفات المشاريع",
    "Project Documents": "مستندات المشروع",
    "Project Analytic Account": "الحساب التحليلي للمشروع",
    "Dates & Contract": "التواريخ والعقد", "Dates & Terms": "التواريخ والشروط",
    "Contract": "العقد", "Contract Duration (days)": "مدة العقد (أيام)",
    "Financial Summary": "الملخص المالي", "Financial Control": "الرقابة المالية",
    "Drive Folder": "مجلد Drive", "Site Warehouse": "مخزن الموقع",
    "Site Location": "موقع المخزون", "Drawings": "الرسومات",
    "Electrical Engineer": "مهندس كهرباء", "Mechanical Engineer": "مهندس ميكانيكا",
    "Logistics Manager": "مدير الحركة", "Finance Manager": "المدير المالي",
    "Finance Responsible": "المسؤول المالي", "Responsible Accountant": "المحاسب المسؤول",
    "HR Supervisor": "مشرف الموارد البشرية", "Assigned Employees": "الموظفون المكلفون",
    "Hold Reason": "سبب الإيقاف", "Held Since": "موقوف منذ",
    "Hold Approved By": "اعتمد الإيقاف", "Hold Requested By": "طلب الإيقاف",
    "Why is the site stopping, and what unblocks it?":
        "لماذا يتوقف الموقع، وما الذي يعيد تشغيله؟",
    "Initial Handover": "التسليم الابتدائي", "Final Handover": "التسليم النهائي",
    "Handover & Closure": "التسليم والإقفال", "Closure Notes": "ملاحظات الإقفال",
    "Overall Progress %": "نسبة الإنجاز الكلية %",

    # ---- profit statement ----
    "Profit Statement": "بيان الأرباح", "Cost Breakdown": "تفصيل التكلفة",
    "Raw Materials": "المواد الخام", "Salaries & Wages": "المرتبات والأجور",
    "Equipment": "المعدات", "Overheads": "المصاريف العمومية",
    "Other Expenses": "مصروفات أخرى", "Direct Purchases": "المشتريات المباشرة",
    "Subcontractor Expenses": "مصروفات مقاولي الباطن",
    "Certified Subcontractor Work": "أعمال مقاولي الباطن المعتمدة",
    "Total Certificates": "إجمالي المستخلصات", "Total Cost": "إجمالي التكلفة",
    "Net Profit": "صافي الربح", "Net Margin (%)": "نسبة صافي الربح (%)",

    # ---- billing ----
    "Billing": "المستخلصات", "RA Billing": "المستخلصات الجارية",
    "Progress Billing": "مستخلصات الإنجاز", "Certificate": "مستخلص",
    "Certificate Line": "بند المستخلص", "Certificate Lines": "بنود المستخلص",
    "Payment Certificates": "المستخلصات",
    "Construction Payment Certificate": "مستخلص أعمال",
    "Construction Certificate": "مستخلص أعمال",
    "Customer Certificate": "مستخلص عميل",
    "Subcontractor Certificate": "مستخلص مقاول باطن",
    "Customer / Subcontractor": "عميل / مقاول باطن",
    "Customer Invoices": "فواتير العملاء", "Vendor Bills": "فواتير الموردين",
    "Invoice / Vendor Bill": "الفاتورة",

    # ---- procurement ----
    "Procurement": "المشتريات", "Purchase Orders": "أوامر الشراء",
    "Purchase Lines": "بنود الشراء", "Requisitions": "طلبات التوريد",
    "Material Requisition": "طلب توريد مواد",
    "Material Requisition Line": "بند طلب التوريد",
    "Material Requisitions": "طلبات توريد المواد",
    "Material Requests": "طلبات المواد", "Materials": "المواد",
    "Preferred Vendor": "المورد المفضل", "Vendor Payment Terms": "شروط سداد المورد",
    "Related Purchase Order": "أمر الشراء المرتبط",
    "Subcontract Purchase Order": "أمر شراء مقاول الباطن",
    "RFQs & POs": "طلبات الأسعار وأوامر الشراء",
    "RFQs / Purchase Orders": "طلبات الأسعار / أوامر الشراء",
    "Subcontract": "تعاقد باطن", "Subcontracts": "مقاولو الباطن",
    "Subcontractor": "مقاول باطن", "Service Product": "منتج الخدمة",

    # ---- planning / execution ----
    "Planning": "التخطيط", "WBS Phase": "مرحلة العمل", "WBS Phases": "مراحل العمل",
    "Phase Details": "بيانات المرحلة", "Parent Phase": "المرحلة الأم",
    "Sub-phases": "المراحل الفرعية", "Work Order": "أمر شغل",
    "Work Orders": "أوامر الشغل", "Work Execution": "تنفيذ الأعمال",
    "Execution Lines": "بنود التنفيذ", "Foreman": "مشرف الموقع",
    "Construction Work Order Execution Line": "بند تنفيذ أمر الشغل",
    "Civil": "أعمال مدنية", "Structural": "أعمال إنشائية", "Electrical": "أعمال كهرباء",
    "Plumbing/MEP": "أعمال صحية وميكانيكا", "Finishing": "تشطيبات",
    "External Works": "أعمال خارجية", "Other": "أخرى",
    "Normal": "عادي", "High": "مرتفع", "Urgent": "عاجل",

    # ---- quality ----
    "Quality": "الجودة", "Quality Check": "فحص جودة", "Quality Checks": "فحوصات الجودة",
    "Quality Checklist Item": "بند قائمة فحص الجودة",
    "Inspection Details": "بيانات الفحص", "Inspector": "الفاحص",
    "Inspector & Type": "الفاحص والنوع", "Final Inspection": "الفحص النهائي",
    "Material Inspection": "فحص المواد", "Workmanship": "جودة التنفيذ",
    "Safety": "السلامة", "Corrective Action": "الإجراء التصحيحي",
    "Remarks & Corrective Action": "الملاحظات والإجراء التصحيحي",
    "Remarks...": "ملاحظات...", "Corrective actions required...": "الإجراءات التصحيحية المطلوبة...",

    # ---- expenses ----
    "Expenses": "المصروفات", "Expense Details": "بيانات المصروف",
    "Construction Expense": "مصروف مشروع", "Incurred By": "تحمَّلها",
    "Labour": "عمالة", "Material": "مواد", "Overhead": "مصاريف عمومية",

    # ---- documents ----
    "Construction Document": "مستند مشروع",
    "Construction Document Type": "نوع مستند المشاريع",
    "Document Type": "نوع المستند", "Document Types": "أنواع المستندات",
    "Required Documents": "المستندات المطلوبة",
    "Missing Documents": "المستندات الناقصة",
    "Documents Ready (%)": "اكتمال المستندات (%)",
    "Required by Default": "مطلوب افتراضياً",
    "Technical File": "الملف الفني", "Financial File": "الملف المالي",
    "Legal File": "الملف القانوني",
    "Technical File Ready": "الملف الفني مكتمل",
    "Financial File Ready": "الملف المالي مكتمل",
    "Technical Office": "المكتب الفني",
    "Technical Office Opinion": "رأي المكتب الفني",
    "Technical Office Reviewer": "مراجع المكتب الفني",
    "Technical Review Date": "تاريخ المراجعة الفنية",
    "Technical specifications, delivery instructions...":
        "المواصفات الفنية وتعليمات التسليم...",

    # ---- HR ----
    "HR Case": "حالة موارد بشرية", "HR Cases": "حالات الموارد البشرية",
    "Construction HR Case": "حالة موارد بشرية بالمشروع",
    "Human Resources": "الموارد البشرية", "Management": "الإدارة",
    "Finance": "المالية", "Appraisal": "تقييم", "Appraisals": "التقييمات",
    "Issue": "مشكلة", "Issues": "المشاكل", "Absence": "غياب", "Warning": "إنذار",
    "Poor": "ضعيف", "Below Expectations": "أقل من المتوقع", "Meets": "مطابق للتوقعات",
    "Exceeds": "أعلى من المتوقع",
    "What happened?": "ماذا حدث؟",

    # ---- app ----
    "Construction": "المقاولات",
    "Construction Dashboard": "لوحة متابعة المقاولات",
    "Amount & Approval": "المبلغ والاعتماد",

    # ---- labels Odoo derives from the field name ----
    "Ref": "المرجع", "State": "الحالة", "Category": "التصنيف", "Priority": "الأولوية",
    "Location": "الموقع", "Remarks": "ملاحظات", "Subtotal": "الإجمالي الفرعي",
    "Currency": "العملة", "Uom": "الوحدة", "Qty": "الكمية", "Line": "البند",
    "Boq": "المقايسة", "Wbs": "مرحلة العمل", "Check": "الفحص",
    "Requisition": "طلب التوريد", "Requested By": "طلبها",
    "Project Code": "كود المشروع", "Tender No.": "رقم المناقصة",
    "Tender Type": "نوع المناقصة", "Item No.": "رقم البند",
    "Certificate No.": "رقم المستخلص", "Work Type": "نوع العمل",
    "Check Type": "نوع الفحص", "Check Date": "تاريخ الفحص",
    "Is Checked": "تم فحصه", "Section Header": "عنوان قسم",
    "Scope Of Work": "نطاق العمل",

    # dates
    "Start Date": "تاريخ البدء", "End Date": "تاريخ الانتهاء",
    "Planned Start": "البدء المخطط", "Planned End": "الانتهاء المخطط",
    "Actual Start": "البدء الفعلي", "Actual End": "الانتهاء الفعلي",
    "Date Requested": "تاريخ الطلب", "Date Required": "التاريخ المطلوب",
    "Billing Date": "تاريخ المستخلص",
    "Billing Period Start": "بداية فترة المستخلص",
    "Billing Period End": "نهاية فترة المستخلص",

    # quantities
    "Planned Qty": "الكمية المخططة", "Executed Qty": "الكمية المنفذة",
    "Accepted Qty": "الكمية المقبولة", "Rejected Qty": "الكمية المرفوضة",
    "Purchased Qty": "الكمية المشتراة", "Contract Qty": "كمية العقد",
    "Current Qty": "كمية الفترة", "Prev. Qty": "الكمية السابقة",
    "Qty Requested": "الكمية المطلوبة", "Qty Approved": "الكمية المعتمدة",
    "Qty Received": "الكمية المستلمة", "Qty Cumulative": "الكمية التراكمية",
    "Qty Remaining": "الكمية المتبقية",
    "Customer Certified Qty": "الكمية المعتمدة للعميل",
    "Subcontract Certified Qty": "الكمية المعتمدة لمقاول الباطن",
    "Remaining Execution Qty": "الكمية المتبقية للتنفيذ",

    # money
    "Unit Rate": "سعر الوحدة", "Unit Cost": "تكلفة الوحدة",
    "Unit Price": "سعر الوحدة", "Cost Rate": "سعر التكلفة",
    "Bid Unit Rate": "سعر وحدة العطاء",
    "Estimated Cost Rate": "سعر التكلفة التقديري",
    "Estimated Bid Value": "قيمة العطاء التقديرية",
    "Estimated Cost": "التكلفة التقديرية", "Estimated Margin": "الهامش التقديري",
    "Estimated Margin Percent": "نسبة الهامش التقديري",
    "Contract Value": "قيمة العقد", "Total Amount": "الإجمالي",
    "Total Estimated Cost": "إجمالي التكلفة التقديرية",
    "Total Expenses": "إجمالي المصروفات", "Purchase Total": "إجمالي المشتريات",
    "Budget Cost": "التكلفة المعتمدة", "Budget Revenue": "الإيراد المعتمد",
    "Budget Margin": "الهامش المعتمد", "Budget Margin Percent": "نسبة الهامش المعتمد",
    "Actual Cost": "التكلفة الفعلية", "Planned Cost": "التكلفة المخططة",
    "Committed Cost": "التكلفة الملتزم بها", "Gross Margin": "مجمل الربح",
    "Forecast Margin": "الهامش المتوقع", "Margin": "الهامش",
    "Invoiced Revenue": "الإيرادات المفوترة",
    "Certified Revenue": "الإيرادات المعتمدة",
    "Certified Amount": "القيمة المعتمدة",
    "Certified Subcontract Cost": "تكلفة الباطن المعتمدة",
    "Billed Amount": "القيمة المفوترة", "Paid Amount": "القيمة المدفوعة",
    "Amount Remaining": "القيمة المتبقية", "Amount Earned": "القيمة المستحقة",
    "Amount Previously Billed": "المفوتر سابقاً",
    "Amount This Period": "قيمة الفترة الحالية",
    "Previous Billed": "المستخلص السابق", "Net Amount": "الصافي",
    "Net Payable": "صافي المستحق", "Other Deductions": "استقطاعات أخرى",
    "Retention %": "نسبة المحتجز %", "Retention Amount": "قيمة المحتجز",
    "Advance %": "نسبة الدفعة المقدمة", "Advance Recovery": "خصم الدفعة المقدمة",
    "Billing Type": "نوع المستخلص",

    # progress
    "% Complete": "نسبة الإنجاز %", "Progress %": "نسبة الإنجاز %",
    "Progress Percent": "نسبة الإنجاز", "Completion Percent": "نسبة الإتمام",

    # counters
    "Billing Count": "عدد المستخلصات", "Boq Count": "عدد المقايسات",
    "Wbs Count": "عدد المراحل", "Work Order Count": "عدد أوامر الشغل",
    "Subcontract Count": "عدد تعاقدات الباطن",
    "Material Requisition Count": "عدد طلبات التوريد",
    "Quality Check Count": "عدد فحوصات الجودة",
    "Expense Count": "عدد المصروفات", "Project Count": "عدد المشاريع",
    "Purchase Order Count": "عدد أوامر الشراء",
    "Vendor Bill Count": "عدد فواتير الموردين",
    "Customer Invoice Count": "عدد فواتير العملاء",

    # reminder flags
    "Reminder Submission Sent": "تم إرسال تذكير التسليم",
    "Reminder Envelope Sent": "تم إرسال تذكير فتح المظاريف",
    "Reminder Award Sent": "تم إرسال تذكير البت",

    # ---- messages shown to the user from code ----
    "Set the tendering authority before asking for approval.":
        "حدد الجهة المالكة قبل طلب الموافقة.",
    "Set the submission deadline before asking for approval.":
        "حدد موعد التسليم قبل طلب الموافقة.",
    "Only a draft tender can be sent for approval.":
        "لا تُرسل للموافقة إلا مناقصة في حالة مسودة.",
    "Only a tender waiting for approval can be approved.":
        "لا يُعتمد إلا ما هو بانتظار موافقة الإدارة.",
    "Only a tender waiting for approval can be rejected.":
        "لا يُرفض إلا ما هو بانتظار موافقة الإدارة.",
    "Only a tender the management has approved and the technical office is studying can be submitted.":
        "لا يُقدَّم العطاء إلا لمناقصة اعتمدتها الإدارة ويدرسها المكتب الفني.",
    "The booklet fee can only be spent after management has approved opening the tender.":
        "لا يُصرف ثمن الكراسة إلا بعد اعتماد الإدارة لفتح العملية.",
    "The bid bond has to be issued before the bid is submitted.":
        "يجب إصدار التأمين الابتدائي قبل تقديم العطاء.",
    "Price the tender items before submitting.":
        "سعّر بنود المناقصة قبل التقديم.",
    "Set the tender document fee first.":
        "حدد ثمن كراسة الشروط أولاً.",
    'Record the initial handover date before closing "%s".':
        'سجّل تاريخ التسليم الابتدائي قبل إقفال "%s".',
    'The performance bond of "%s" has not been released yet.':
        'التأمين النهائي لـ "%s" لم يُرد بعد.',
    '"%(project)s" still has %(count)s payment certificate(s) that are neither approved nor cancelled.':
        '"%(project)s" ما زال به %(count)s مستخلص غير معتمد وغير ملغي.',
    "Only a running project can move to handover.":
        "لا ينتقل للتسليم إلا مشروع جارٍ.",
    '"%s" already exists.': '"%s" موجود بالفعل.',

    # chatter and activity messages
    "Opening approved. Budget released: %(budget)s.":
        "تم اعتماد فتح العملية. المبلغ المفرج عنه: %(budget)s.",
    "Opening rejected. Reason: %s": "تم رفض فتح العملية. السبب: %s",
    "Approve opening of tender %s": "اعتماد فتح المناقصة %s",
    "Requested budget: %(budget)s. Submission deadline: %(deadline)s.":
        "المبلغ المطلوب: %(budget)s. موعد التسليم: %(deadline)s.",
    "Answered by management.": "تم الرد من الإدارة.",
    "Conditions booklet purchased for %s.": "تم شراء كراسة الشروط بمبلغ %s.",
    "Tender lost. Kept open until the bid bond of %s is released.":
        "خسرنا المناقصة. تبقى مفتوحة حتى يُرد التأمين الابتدائي %s.",
    "Bid bond released.": "تم رد التأمين الابتدائي.",
    "Bid bond forfeited: %s.": "تمت مصادرة التأمين الابتدائي: %s.",
    "Performance bond released.": "تم رد التأمين النهائي.",
    "Project put on hold. Reason: %s": "تم إيقاف المشروع. السبب: %s",
    "%(label)s for %(tender)s": "%(label)s لـ %(tender)s",
    "Due on %s.": "الموعد %s.",
    "Tender document fee - %s": "ثمن كراسة الشروط - %s",

    # window titles opened from code
    "Reject Tender": "رفض المناقصة",
    "Hold Project": "إيقاف المشروع",
    "Project Documents": "مستندات المشروع",
    "Tender Document Fee": "ثمن كراسة الشروط",
    "HR Cases": "حالات الموارد البشرية",
    "Only the construction management can answer a request to open an operation.":
        "لا يرد على طلب فتح العملية إلا إدارة المقاولات.",
    "Tender Document Fee For": "ثمن كراسة شروط لـ",
    "Conditions booklet fee settled by %s.": "تم سداد ثمن كراسة الشروط بالسند %s.",
    "Refresh from Tender": "تحديث من المناقصة",
    "This project did not come from a tender.": "هذا المشروع لم يأتِ من مناقصة.",
    "The tender has nothing filled in that the project is missing.":
        "لا يوجد في المناقصة بيان ناقص لدى المشروع.",
    "Refreshed from tender %s.": "تم التحديث من المناقصة %s.",
    # ---- subcontract assignment ----
    "Subcontract Item": "بند إسناد",
    "Assigned Items": "البنود المسندة",
    "Subcontract Assignments": "الإسنادات",
    "BOQ Item": "بند المقايسة",
    "BOQ Quantity": "كمية المقايسة",
    "Selling Rate": "سعر البيع",
    "Own Cost Rate": "سعر التكلفة عندنا",
    "Assigned Quantity": "الكمية المسندة",
    "Subcontractor Rate": "سعر المقاول",
    "Assigned Value": "قيمة الإسناد",
    "Assigned Cost": "تكلفة الإسناد",
    "Unassigned Quantity": "الكمية غير المسندة",
    "Over-assigned": "إسناد زائد",
    "Item Margin": "هامش البند",
    "Item Margin (%)": "هامش البند (%)",
    "Margin on Assignment": "هامش الإسناد",
    "Margin (%)": "الهامش (%)",
    "Margin after Subcontracting": "الهامش بعد الإسناد",
    "Margin after Subcontracting (%)": "الهامش بعد الإسناد (%)",
    "Certified Quantity": "الكمية المعتمدة",
    "Remaining Quantity": "الكمية المتبقية",
    "Add Unassigned BOQ Items": "إضافة بنود المقايسة غير المسندة",
    "Item": "بند",
    "Progress (%)": "نسبة الإنجاز (%)",
    "Completed Quantity": "الكمية المنجزة",
    "Quantity to Certify": "الكمية المستحقة",
    "Value to Certify": "القيمة المستحقة",
    "Subcontractor Certificate": "مستخلص مقاول باطن",
    "Certificate - %s": "مستخلص - %s",
    "Nothing new to certify. Set the progress on the assigned items first.":
        "لا يوجد جديد للاستخلاص. حدد نسبة الإنجاز على البنود المسندة أولاً.",
    "Certify Progress": "استخلاص الإنجاز",
    "Blank Certificate": "مستخلص فارغ",
    "New Certificate": "مستخلص فارغ",
    "Done In-house": "منجز ذاتياً",
    "Done by Subcontractors": "منجز بالباطن",
    "In-house Scope": "نصيب التنفيذ الذاتي",
    "Still Available": "المتاح للتخطيط",
    # ---- validation messages from the base module ----
    "Accepted quantity cannot exceed executed quantity.":
        "الكمية المقبولة لا تتجاوز الكمية المنفذة.",
    "Accepted quantity exceeds the BOQ contract quantity.":
        "الكمية المقبولة تتجاوز كمية المقايسة التعاقدية.",
    "Work order quantities cannot be negative.":
        "كميات أمر الشغل لا تكون بالسالب.",
    "Cumulative quantity cannot exceed contract quantity.":
        "الكمية التراكمية لا تتجاوز الكمية التعاقدية.",
    "Contract value cannot be negative.": "قيمة العقد لا تكون بالسالب.",
    "Net payable cannot be negative.": "صافي المستحق لا يكون بالسالب.",
    "End date cannot be earlier than start date.":
        "تاريخ الانتهاء لا يسبق تاريخ البدء.",
    "Billing period end cannot be earlier than start.":
        "نهاية فترة المستخلص لا تسبق بدايتها.",
    "Required date cannot be earlier than request date.":
        "التاريخ المطلوب لا يسبق تاريخ الطلب.",
    "Submission deadline cannot be earlier than the issue date.":
        "موعد التسليم لا يسبق تاريخ الإصدار.",

    "Add at least one material line before submitting.":
        "أضف بند مواد واحداً على الأقل قبل التقديم.",
    "Add at least one priced item before submitting the tender.":
        "أضف بنداً مسعّراً واحداً على الأقل قبل تقديم المناقصة.",
    "Add certificate lines before submitting.":
        "أضف بنود المستخلص قبل التقديم.",
    "Add tender items before converting to a project.":
        "أضف بنود المناقصة قبل تحويلها إلى مشروع.",
    "This tender has already been converted into a project.":
        "هذه المناقصة تم تحويلها إلى مشروع بالفعل.",
    "Approve the certificate first.": "اعتمد المستخلص أولاً.",
    "The requisition must be approved before creating an RFQ.":
        "يجب اعتماد طلب التوريد قبل إنشاء طلب عرض السعر.",
    "Select a preferred vendor first.": "اختر المورد المفضل أولاً.",
    "Select a service product for the subcontract.":
        "اختر منتج الخدمة الخاص بتعاقد الباطن.",
    "No approved product quantities are available.":
        "لا توجد كميات معتمدة متاحة.",

    # report and record labels built in code
    "%s - Initial BOQ": "%s - المقايسة المبدئية",
    "%s Certificate": "مستخلص %s",
    "Subcontractor Certificates": "مستخلصات مقاولي الباطن",
    "Retention Deduction": "خصم المحتجز",
    "Pricing": "التسعير",
    "No.": "م",
    "Quantity": "الكمية",
    "Unit": "الوحدة",
    "Total": "الإجمالي",
    "Profit %": "نسبة الربح %",
    "Contingency %": "نسبة الطوارئ %",
    "Administration %": "نسبة الإدارة %",
    "Expenses %": "نسبة المصاريف %",
    # ---- labour and shifts ----
    "Labour Type": "نوع العمالة",
    "Labour Types": "أنواع العمالة",
    "Labour Requirement": "تقدير العمالة",
    "Labour & Shifts": "العمالة والورديات",
    "Trade": "الحرفة",
    "Crew Size": "عدد أفراد الوردية",
    "Shifts": "عدد الورديات",
    "Man-shifts": "ورديات الأفراد",
    "Hours per Shift": "ساعات الوردية",
    "Total Hours": "إجمالي الساعات",
    "Rate per Person / Shift": "أجر الفرد للوردية",
    "Default Shift Rate": "أجر الوردية الافتراضي",
    "Estimated Cost": "التكلفة التقديرية",
    "Estimated Labour Cost": "تكلفة العمالة التقديرية",
    "Actual Labour Cost": "تكلفة العمالة الفعلية",
    "Labour Left to Spend": "المتبقي من موازنة العمالة",
    "Operating Cost in Prices": "تكلفة التشغيل داخل الأسعار",
    "Labour Headroom": "فائض موازنة العمالة",
    "Labour Headroom (%)": "فائض موازنة العمالة (%)",
    "Labour Over Budget": "العمالة تتجاوز الموازنة",
    "Review": "المراجعة",
    "Effort": "المجهود",
    "Site Foreman": "مشرف موقع",
    "Mason": "بنّاء",
    "Steel Fixer": "حدّاد تسليح",
    "Carpenter": "نجار مسلح",
    "Electrician": "كهربائي",
    "Plumber": "سبّاك",
    "Finishing Worker": "عامل تشطيبات",
    "Helper": "مساعد",
    "Equipment Operator": "مشغّل معدة",
    "Driver": "سائق",
    "In-house Work at Cost": "قيمة التنفيذ الذاتي بالتكلفة",
    "In-house Cost Variance": "فرق تكلفة التنفيذ الذاتي",
    "In-house Execution Control": "رقابة التنفيذ الذاتي",
    "Earned Cost": "التكلفة المكتسبة",
    "Cost Variance": "فرق التكلفة",
    "Actual Unit Cost": "تكلفة الوحدة الفعلية",
    "Purchases": "المشتريات",
    "Labour": "العمالة",
    "Other Costs": "تكاليف أخرى",
    "In-house Actual Cost": "التكلفة الفعلية للتنفيذ الذاتي",
    "Work Order": "أمر الشغل",
    "Expected Cost": "التكلفة المتوقعة",
    "Expected Margin": "الهامش المتوقع",
    "Expected Margin (%)": "الهامش المتوقع (%)",
    "Forecast Cost at Completion": "التكلفة المتوقعة عند الإتمام",
    "Forecast Margin": "الربح المتوقع",
    "Forecast at Completion": "التوقع عند الإتمام",
    "Traced to Work Orders": "المنسوب لأوامر الشغل",
    "Not Traced to an Item": "غير منسوب لبند",
    "Cost Traceability": "تتبّع التكلفة",
    "Subcontractor Cost Counted Twice": "تكلفة الباطن محسوبة مرتين",
    "Technical Envelope Opening": "موعد فتح المظاريف الفني",
    "Financial Award Decision": "موعد البت المالي",
    "Technical envelope opening": "فتح المظاريف الفني",
    "Financial award decision": "البت المالي",
    "Tax (%)": "نسبة الضريبة (%)",
    "Tax Value": "قيمة الضريبة",
    "Price before Tax": "السعر قبل الضريبة",
    "Performance Bond": "التأمين النهائي",
    "What is left, and what was agreed on handover...":
        "ما تبقى، وما تم الاتفاق عليه عند التسليم...",
    "Administrative Handover": "التسليم الإداري",
    "Headroom to Cost": "المتاح حتى سعر التكلفة",
    'The subcontractor rate for "%(item)s" is %(rate)s, above the %(budget)s the item was priced to cost.\nEither negotiate the rate down, or correct the item cost in the bill of quantities if the estimate was wrong.':
        'سعر المقاول لـ "%(item)s" هو %(rate)s، وهو أعلى من %(budget)s التي سُعّر البند على أساسها.\nإما أن تفاوض على خفض السعر، أو تصحح تكلفة البند في المقايسة إذا كان التقدير خاطئاً.',
    "These required documents are still missing:\n%s":
        "المستندات المطلوبة الآتية ما زالت ناقصة:\n%s",
    "These documents have expired:\n%s":
        "المستندات الآتية منتهية الصلاحية:\n%s",
    "Set the service product on the subcontract, or on these BOQ items, before raising a certificate:\n%s":
        "حدد منتج الخدمة على تعاقد الباطن، أو على بنود المقايسة الآتية، قبل إصدار مستخلص:\n%s",
    "Tax %": "نسبة الضريبة %",
    # ---- salary distribution ----
    "Salary Distribution": "توزيع الرواتب",
    "Salary Distributions": "توزيعات الرواتب",
    "Salary Allocation": "تحميل راتب",
    "Allocations": "التحميلات",
    "Monthly Cost to Projects": "التكلفة الشهرية المحمّلة على المشاريع",
    "Monthly Cost": "التكلفة الشهرية",
    "Share (%)": "نسبة التحميل (%)",
    "Allocated": "المحمّل",
    "Total Allocated": "إجمالي المحمّل",
    "Period": "الفترة",
    "From": "من",
    "To": "إلى",
    "Post to Projects": "ترحيل على المشاريع",
    "Posted": "مُرحّل",
    "Expense": "المصروف",
    "September 2026": "سبتمبر ٢٠٢٦",
    "How the shares were decided this month...":
        "كيف تم تحديد النسب هذا الشهر...",
    "The period ends before it starts.": "الفترة تنتهي قبل أن تبدأ.",
    "Only a draft distribution can be posted.":
        "لا يُرحَّل إلا توزيع في حالة مسودة.",
    "Add the allocations before posting.": "أضف التحميلات قبل الترحيل.",
    "A share cannot be negative.": "نسبة التحميل لا تكون بالسالب.",
    "%(employee)s - %(period)s": "%(employee)s - %(period)s",
    "%(percent)s%% of the monthly cost of %(employee)s.":
        "%(percent)s%% من التكلفة الشهرية لـ %(employee)s.",
    "%(employee)s is allocated %(total)s%% across the projects in this period, which is more than a whole month.":
        "%(employee)s محمّل بنسبة %(total)s%% على مشاريع هذه الفترة، وهي أكثر من شهر كامل.",
    "Some expenses from this distribution are no longer in the approved state. Handle them by hand before resetting.":
        "بعض مصروفات هذا التوزيع لم تعد في حالة معتمد. عالجها يدوياً قبل إعادة التعيين.",
    "Bond Not Released": "التأمين لم يُرد",
    "Rejected": "مرفوضة",
    "On Hold": "موقوف",
    "Expired": "منتهي",
    "Archived": "مؤرشف",
    "Certify Progress": "استخلاص الإنجاز",
    "Customer Certificate": "مستخلص عميل",
    "Value to Certify": "القيمة المستحقة",
    "Nothing new to certify. Record progress on the bill of quantities first.":
        "لا يوجد جديد للاستخلاص. سجّل الإنجاز على المقايسة أولاً.",
    "Set the product on these BOQ items before raising a certificate:\n%s":
        "حدد المنتج على بنود المقايسة الآتية قبل إصدار مستخلص:\n%s",
    # ---- seeded configuration records ----
    "Endowments Authority": "هيئة الأوقاف",
    "Agricultural Company": "شركة زراعية",
    "Military Entity": "جهة عسكرية",
    "Private Owner": "مالك خاص",

    "Commercial Register": "سجل تجاري",
    "Tax Card": "بطاقة ضريبية",
    "VAT Registration Certificate": "شهادة تسجيل ضريبة القيمة المضافة",
    "Contractors Classification Certificate": "شهادة تصنيف المقاولين",
    "Record of Similar Works": "بيان أعمال مماثلة",
    "Technical Staff and Equipment List": "بيان العمالة الفنية والمعدات",
    "Conditions Booklet (stamped)": "كراسة الشروط مختومة",
    "Priced Schedule of Quantities": "جدول الكميات المسعّر",
    "Bank Solvency Letter": "خطاب ملاءة بنكي",
    "Signed Contract": "العقد الموقّع",
    "Award Letter": "خطاب الترسية",
    "Contract Bill of Quantities": "مقايسة العقد",
    "Construction Drawings": "الرسومات التنفيذية",
    "Site Handover Minutes": "محضر تسليم الموقع",
    "Work orders accept %(accepted)s of \"%(item)s\", but only %(scope)s is ours to execute: %(assigned)s of the %(qty)s in the bill is assigned to subcontractors.\nReduce the assignment first if we are doing this work ourselves.":
        "أوامر الشغل تقبل %(accepted)s من \"%(item)s\"، والمتاح لنا %(scope)s فقط: %(assigned)s من %(qty)s في المقايسة مسندة لمقاولي الباطن.\nقلّل الإسناد أولاً إذا كنا سننفذ هذا العمل بأنفسنا.",
    "Advance (%)": "الدفعة المقدمة (%)",
    "Advance Amount": "قيمة الدفعة المقدمة",
    "Advance Outstanding": "المتبقي من الدفعة المقدمة",
    "Advance Recovered": "المسترد من الدفعة المقدمة",
    "Distribution": "التوزيع",
    "Progress": "نسبة الإنجاز",
    "Progress on \"%(item)s\" is %(percent)s%%. It has to be between 0 and 100.":
        "نسبة الإنجاز في \"%(item)s\" هي %(percent)s%%، ويجب أن تكون بين 0 و100.",
    "Recovering %(recovery)s exceeds the %(outstanding)s of advance still outstanding on this contract.":
        "استرداد %(recovery)s يتجاوز %(outstanding)s المتبقية من الدفعة المقدمة على هذا العقد.",
    "%(later)s is dated %(later_date)s, before the %(earlier)s on %(earlier_date)s. Handover runs provisional, then administrative, then final.":
        "%(later)s مؤرخ في %(later_date)s، أي قبل %(earlier)s في %(earlier_date)s. التسليم يتم ابتدائي ثم إداري ثم نهائي.",
    "The performance bond on %(project)s secures the works until final acceptance. Record the final handover date before releasing it.":
        "خطاب ضمان حسن التنفيذ في %(project)s يغطي الأعمال حتى الاستلام النهائي. سجّل تاريخ التسليم النهائي قبل الإفراج عنه.",
    "Approved payment certificates": "المستخلصات المعتمدة",
    "Authorised Signature": "التوقيع المعتمد",
    "BILL OF QUANTITIES": "جدول الكميات",
    "BOQ Ref:": "مرجع المقايسة:",
    "Bid bond attached": "خطاب التأمين الابتدائي مرفق",
    "Checked By": "روجع بواسطة",
    "Client Advance": "الدفعة المقدمة من العميل",
    "Client:": "العميل:",
    "Contract value": "قيمة العقد",
    "Date:": "التاريخ:",
    "Execution Period": "مدة التنفيذ",
    "For and on behalf of": "بالنيابة عن",
    "Forecast at completion": "التوقع حتى الإنجاز",
    "Forecast cost at completion": "التكلفة المتوقعة حتى الإنجاز",
    "Forecast margin": "الهامش المتوقع",
    "GRAND TOTAL": "الإجمالي العام",
    "Net margin": "نسبة صافي الربح",
    "Net profit": "صافي الربح",
    "Prepared By": "أُعِدّ بواسطة",
    "Pricing Build-up": "بناء السعر",
    "Project Manager:": "مدير المشروع:",
    "Project Profit Statement": "بيان أرباح المشروع",
    "Project:": "المشروع:",
    "Status:": "الحالة:",
    "Total cost": "إجمالي التكلفة",
    "Total offer value": "إجمالي قيمة العطاء",
    "days": "يوم",
    "of which invoiced": "منها مفوتر",
    "Having examined the conditions booklet, the drawings and the schedule of quantities of the above operation, we offer to execute the whole of the works described therein for the total sum stated below, within the period stated above and in accordance with the tender conditions.":
        "بعد أن اطلعنا على كراسة الشروط والمواصفات والرسومات وجدول الكميات الخاص بالعملية الموضحة أعلاه، نتقدم بعطائنا لتنفيذ كامل الأعمال الواردة بها بالمبلغ الإجمالي المبيَّن أدناه، وخلال المدة المحددة أعلاه، ووفقاً لشروط المناقصة.",
    "This offer remains valid and binding upon us for the period stated in the tender conditions, and may be accepted at any time before it expires.":
        "هذا العطاء سارٍ وملزم لنا خلال المدة المنصوص عليها في شروط المناقصة، ويجوز قبوله في أي وقت قبل انتهائها.",
    "Net profit compares what has been certified to the client against the cost incurred so far, so both sides cover the same work. Forecast margin looks ahead instead: the whole contract against what the remaining work is expected to cost, with assigned items at the subcontractors rates and the rest at our own.":
        "صافي الربح يقارن ما استُخلص للعميل بالتكلفة المنصرفة حتى الآن، فيكون الطرفان عن نفس الأعمال. أما الهامش المتوقع فينظر للأمام: قيمة العقد كاملة مقابل التكلفة المتوقعة لما تبقى من أعمال، بأسعار مقاولي الباطن للبنود المسندة وبتكلفتنا لما عداها.",
    "The crews planned cost more than the item prices allow for execution. Either the rates in the prices are too low, or the crews are too many.":
        "تكلفة الطواقم المخططة أعلى من المسموح به في تسعير البنود. إما أن الفئات في التسعير منخفضة، أو أن الطواقم أكثر من اللازم.",
    "This project carries both subcontractor certificates and expenses filed under the subcontractor category, so the same money is very likely counted twice above.":
        "هذا المشروع يحمل مستخلصات لمقاولي الباطن ومصروفات مسجَّلة تحت فئة مقاولي الباطن في نفس الوقت، ومن المرجح جداً أن نفس المبلغ محسوب مرتين أعلاه.",
    "This project carries both subcontractor certificates and expenses filed under the subcontractor category, so the same money is very likely counted twice. Record subcontractor cost one way only.":
        "هذا المشروع يحمل مستخلصات لمقاولي الباطن ومصروفات مسجَّلة تحت فئة مقاولي الباطن في نفس الوقت، ومن المرجح جداً أن نفس المبلغ محسوب مرتين. سجّل تكلفة مقاولي الباطن بطريقة واحدة فقط.",
    "Offer for:": "عطاء عن:",
    "Subtotal (": "الإجمالي الجزئي (",
    "Notes:": "ملاحظات:",
    "| Priority:": "| الأولوية:",
    "Estimated Unit Cost": "التكلفة التقديرية للوحدة",
    "Item Cost Rate": "تكلفة وحدة البند",
    "Against Estimate": "الفرق عن التقدير",
    "What this material is expected to cost, for approving the request against the budget. The price comes from the vendor on the purchase order.":
        "المتوقع أن تكلفه هذه المادة، لاعتماد الطلب في حدود الميزانية. السعر نفسه يأتي من المورد على أمر الشراء.",
    "The rate the bill of quantities item was priced on.":
        "الفئة التي سُعّر بند المقايسة على أساسها.",
    "What the material requisition expected this to cost. Compare it with the price the vendor quoted.":
        "ما توقعه طلب التوريد أن تكلفه. قارنه بالسعر الذي قدّمه المورد.",
    "Estimate less quoted price, per unit. Negative means the vendor is dearer than the request assumed.":
        "التقدير ناقص السعر المعروض، للوحدة. السالب يعني أن المورد أغلى من افتراض الطلب.",
    "Accepted on work orders, counted only up to the part of the item that was not handed to a subcontractor.":
        "المقبول في أوامر الشغل، محسوباً في حدود الجزء غير المسند لمقاول باطن فقط.",
    "Accepted quantity at the item cost rate: what it should have cost.":
        "الكمية المقبولة بتكلفة وحدة البند: ما كان يجب أن تكلفه.",
    "Accepted work valued at the item cost rates: what it should have cost.":
        "الأعمال المقبولة مقيَّمة بتكلفة وحدات البنود: ما كان يجب أن تكلفه.",
    "Advance still to be recovered from this party before this certificate.":
        "المتبقي من الدفعة المقدمة الواجب استرداده من هذا الطرف قبل هذا المستخلص.",
    "Allowance for unforeseen site conditions and price variations.":
        "مخصص للظروف غير المتوقعة في الموقع وتغيّر الأسعار.",
    "Approved expenses booked as labour.": "المصروفات المعتمدة المسجَّلة كعمالة.",
    "Approved labour expenses booked against this item.": "مصروفات العمالة المعتمدة المسجَّلة على هذا البند.",
    "Approved overhead and miscellaneous expenses booked against this item.":
        "المصروفات العامة والمتنوعة المعتمدة المسجَّلة على هذا البند.",
    "Bid bond this authority normally asks for.": "التأمين الابتدائي الذي تطلبه هذه الجهة عادةً.",
    "Build the rate from cost and ratios. Uncheck to type the cost and selling rates by hand, for items quoted as a lump sum.":
        "بناء السعر من التكلفة والنسب. أزل التحديد لإدخال التكلفة وسعر البيع يدوياً، للبنود المسعّرة بالمقطوعية.",
    "Cash the tender needs up front: booklet fee, bond and study costs. This is what management approves.":
        "النقدية التي تحتاجها المناقصة مقدماً: قيمة الكراسة والتأمين وتكاليف الدراسة. هذا ما توافق عليه الإدارة.",
    "Certified to subcontractors, counted only up to what they were assigned.":
        "المعتمد لمقاولي الباطن، محسوباً في حدود ما أُسند إليهم فقط.",
    "Completed less already certified: what the next certificate covers.":
        "المنفَّذ ناقص ما استُخلص سابقاً: ما يغطيه المستخلص القادم.",
    "Completed value against assigned value, so a big item counts for more than a small one.":
        "قيمة المنفَّذ مقابل قيمة المسند، فيكون للبند الكبير وزن أكبر من الصغير.",
    "Contract value less the forecast cost: the profit the project is heading for, rather than the profit booked so far.":
        "قيمة العقد ناقص التكلفة المتوقعة: الربح الذي يتجه إليه المشروع، لا الربح المحقق حتى الآن.",
    "Crew size times shifts: the labour the estimate commits to.": "عدد الطاقم × عدد الورديات: العمالة التي يلتزم بها التقدير.",
    "Date the client took provisional delivery of the works.": "تاريخ استلام العميل للأعمال استلاماً ابتدائياً.",
    "Date the maintenance period ended and the works were finally accepted.":
        "تاريخ انتهاء فترة الصيانة والاستلام النهائي للأعمال.",
    "Date the works were handed to the body that will operate them, between provisional and final acceptance.":
        "تاريخ تسليم الأعمال للجهة التي ستشغّلها، بين الاستلام الابتدائي والنهائي.",
    "Default bid bond percentage of the estimated bid value.": "النسبة الافتراضية للتأمين الابتدائي من قيمة العطاء التقديرية.",
    "Default performance bond percentage of the contract value.": "النسبة الافتراضية لضمان حسن التنفيذ من قيمة العقد.",
    "Dry cost plus operating cost, before any markup.": "تكلفة الخامات زائد تكلفة التشغيل، قبل أي إضافة.",
    "Earned cost less what was actually spent. Negative means the work cost more than the rates allowed.":
        "التكلفة المكتسبة ناقص ما أُنفق فعلاً. السالب يعني أن العمل كلّف أكثر مما تسمح به الفئات.",
    "Earned less actual. A negative figure means our own work is costing more than the item rates allowed.":
        "المكتسبة ناقص الفعلية. الرقم السالب يعني أن تنفيذنا الذاتي يكلّف أكثر مما تسمح به فئات البنود.",
    "Endowment, agricultural company, ministry, private owner... It drives the paperwork and the bid bond the client expects.":
        "هيئة أوقاف، شركة زراعية، وزارة، مالك خاص... تحدد المستندات والتأمين الابتدائي الذي يطلبه العميل.",
    "Engineers the technical office asks to be freed for the study.":
        "المهندسون الذين يطلب المكتب الفني تفريغهم للدراسة.",
    "Executed quantity less the quantity in the bill of quantities. A positive figure is work done beyond what the client priced.":
        "الكمية المنفَّذة ناقص كمية المقايسة. الرقم الموجب يعني أعمالاً نُفِّذت زيادة على ما سعّره العميل.",
    "Execution period agreed in the contract.": "مدة التنفيذ المتفق عليها في العقد.",
    "Execution period the tender conditions allow, counted from the site handover.":
        "مدة التنفيذ التي تسمح بها شروط المناقصة، محسوبة من تسليم الموقع.",
    "Filled in for appraisals.": "تُستكمل في حالات التقييم.",
    "General expenses applied on the marked-up price, the last step of the build-up.":
        "المصروفات العامة المطبَّقة على السعر بعد الإضافات، آخر خطوة في بناء السعر.",
    "Government bodies usually require a bid bond and a classification certificate.":
        "الجهات الحكومية تطلب عادةً تأميناً ابتدائياً وشهادة تصنيف.",
    "How many days before a tender date the responsible users are reminded.":
        "عدد الأيام قبل موعد المناقصة التي يُنبَّه فيها المسؤولون.",
    "How many shifts this crew is needed for.": "عدد الورديات المطلوبة لهذا الطاقم.",
    "How much of this item the engineer accepts as complete. This is what the next certificate is measured from.":
        "ما يعتمده المهندس من هذا البند كمنفَّذ. هذا هو الأساس الذي يُقاس عليه المستخلص القادم.",
    "In-house execution plus certified subcontract work. Each side is capped at its own share of the item, so an item that is part self-performed and part subcontracted is never counted twice.":
        "التنفيذ الذاتي زائد أعمال الباطن المعتمدة. كل جانب محدود بنصيبه من البند، فالبند المنفَّذ جزء ذاتياً وجزء بالإسناد لا يُحسب مرتين.",
    "In-house scope less what other work orders already plan for this item.":
        "نصيبنا من البند ناقص ما تخططه أوامر شغل أخرى لهذا البند.",
    "Incurred cost with no work order or item on it. The higher this is, the less the item-level costing can be trusted.":
        "تكلفة منصرفة بلا أمر شغل ولا بند. كلما زادت، قلّت الثقة في تكلفة البنود.",
    "Labour, equipment and execution cost of putting one unit in place.":
        "تكلفة العمالة والمعدات والتنفيذ لوضع وحدة واحدة في موقعها.",
    "Leave empty for crews that serve the whole site.": "اتركه فارغاً للطواقم التي تخدم الموقع بالكامل.",
    "Link to the shared folder holding the contract, the BOQ and the drawings.":
        "رابط المجلد المشترك الذي يضم العقد والمقايسة والرسومات.",
    "Loaded as a required line when the standard checklist is pulled onto a tender or a project.":
        "يُحمَّل كسطر مطلوب عند تحميل القائمة القياسية على مناقصة أو مشروع.",
    "Material cost of one unit, at the price the purchasing department can buy it today.":
        "تكلفة خامات الوحدة الواحدة، بالسعر الذي يمكن لقسم المشتريات الشراء به اليوم.",
    "Money the project has actually incurred: approved expenses, subcontractor work certified to date, and purchases received against the project.":
        "ما أنفقه المشروع فعلاً: المصروفات المعتمدة، وأعمال مقاولي الباطن المستخلصة حتى تاريخه، والمشتريات المستلمة على المشروع.",
    "More of this item has been handed to subcontractors than the bill of quantities carries.":
        "المسند لمقاولي الباطن من هذا البند أكبر من الكمية الموجودة في المقايسة.",
    "Net profit added on top of the item cost.": "صافي الربح المضاف على تكلفة البند.",
    "Operating cost in the prices, less the labour actually planned. A negative figure means the crews cost more than the bid allows.":
        "تكلفة التشغيل في التسعير ناقص العمالة المخططة فعلاً. الرقم السالب يعني أن الطواقم تكلّف أكثر مما يسمح به العطاء.",
    "Our own cost rate for the item less what the subcontractor charges. What is left of the item budget before handing it out starts eating the priced margin.":
        "تكلفة وحدة البند عندنا ناقص ما يأخذه المقاول. المتبقي من ميزانية البند قبل أن يبدأ الإسناد في أكل الهامش المسعَّر.",
    "Owns plant movement and transport between sites.": "مسؤول عن حركة المعدات والنقل بين المواقع.",
    "Paid up front against the contract and recovered from the certificates as work is done.":
        "تُدفع مقدماً على العقد وتُسترد من المستخلصات مع تقدم الأعمال.",
    "Papers such as the tax card or the classification certificate carry an expiry date that has to be valid on submission day.":
        "مستندات مثل البطاقة الضريبية أو شهادة التصنيف لها تاريخ انتهاء يجب أن يكون سارياً يوم التقديم.",
    "People of this trade working one shift.": "عدد أفراد هذه المهنة في الوردية الواحدة.",
    "Profit + contingency + administration.": "الربح + الطوارئ + المصروفات الإدارية.",
    "Purchase orders booked on the project, excluding those raised against a subcontract, which the subcontractor certificates already account for.":
        "أوامر الشراء المسجَّلة على المشروع، باستثناء المُصدرة على عقد باطن لأن مستخلصات المقاول تحسبها بالفعل.",
    "Purchase orders, plus material and equipment expenses, booked against this item on this work order.":
        "أوامر الشراء، ومعها مصروفات الخامات والمعدات، المسجَّلة على هذا البند في أمر الشغل هذا.",
    "Purchases, wages and expenses actually booked against the work orders.":
        "المشتريات والأجور والمصروفات المسجَّلة فعلاً على أوامر الشغل.",
    "Quantity of this item already certified to the subcontractor.":
        "الكمية المعتمدة لمقاول الباطن من هذا البند.",
    "Received from the client up front and recovered from the payment certificates as work is done.":
        "تُستلم من العميل مقدماً وتُسترد من المستخلصات مع تقدم الأعمال.",
    "Recovered in proportion to the work certified, and never more than the advance still outstanding. Edit it if the contract recovers on a different schedule.":
        "يُسترد بنسبة الأعمال المستخلصة، وبما لا يتجاوز المتبقي من الدفعة المقدمة. عدّله إذا كان العقد يسترد بجدول مختلف.",
    "Share of head office administration carried by the item.": "نصيب البند من المصروفات الإدارية للمركز الرئيسي.",
    "Share of the contract the client pays up front.": "نسبة العقد التي يدفعها العميل مقدماً.",
    "Sum of the items handed to this subcontractor.": "مجموع البنود المسندة لمقاول الباطن هذا.",
    "Taken from the employee, and editable for a month that differs.":
        "تأتي من كارت الموظف، وقابلة للتعديل في شهر يختلف.",
    "Taxes priced into the rate, picked from the taxes defined on the system. Percentage taxes only; a fixed-amount tax cannot be built into a unit rate.":
        "الضرائب المحمَّلة على السعر، تُختار من الضرائب المعرَّفة على النظام. الضرائب النسبية فقط؛ الضريبة ذات المبلغ الثابت لا يمكن بناؤها داخل سعر وحدة.",
    "The accountant who owns this project file.": "المحاسب المسؤول عن ملف هذا المشروع.",
    "The assigned quantity at what the subcontractors charge, plus the rest at our own cost rate. What the item will cost once it is done, rather than what it was budgeted at.":
        "الكمية المسندة بأسعار مقاولي الباطن، والباقي بتكلفتنا. ما سيكلفه البند عند انتهائه، لا ما كان مقدَّراً له.",
    "The part of the BOQ item that was not handed to a subcontractor, so it is ours to execute.":
        "الجزء من بند المقايسة غير المسند لمقاول باطن، وهو نصيبنا في التنفيذ.",
    "The part of the incurred cost that carries a work order and an item. Part of the total, never added to it.":
        "الجزء من التكلفة المنصرفة الذي يحمل أمر شغل وبنداً. جزء من الإجمالي ولا يُضاف إليه.",
    "The payment that settled the booklet fee.": "الدفعة التي سُدِّدت بها قيمة الكراسة.",
    "The priced tender item this BOQ item was created from.": "بند المناقصة المسعَّر الذي أُنشئ منه بند المقايسة هذا.",
    "The project carries both subcontractor certificates and expenses filed under the subcontractor category, so the same money is very likely counted twice.":
        "المشروع يحمل مستخلصات لمقاولي الباطن ومصروفات مسجَّلة تحت فئة مقاولي الباطن، ومن المرجح جداً أن نفس المبلغ محسوب مرتين.",
    "The tender whose conditions booklet this payment pays for. Settling the payment marks the booklet as purchased.":
        "المناقصة التي تُسدَّد بهذه الدفعة قيمة كراسة شروطها. تسوية الدفعة تُعلّم الكراسة كمُشتراة.",
    "The work order this purchase serves. Filled from the material requisition, and editable for a purchase raised directly.":
        "أمر الشغل الذي يخدمه هذا الشراء. يُملأ من طلب التوريد، وقابل للتعديل في الشراء المباشر.",
    "Total certificates less total cost.": "إجمالي المستخلصات ناقص إجمالي التكلفة.",
    "Value of the payment certificates approved for the client.": "قيمة المستخلصات المعتمدة للعميل.",
    "Value the client states in the tender announcement.": "القيمة التي يعلنها العميل في إعلان المناقصة.",
    "Warehouse the site draws its materials from.": "المخزن الذي يصرف منه الموقع مواده.",
    "Weighted by item value, so a large item moves the phase more than a small one.":
        "مرجَّحة بقيمة البند، فالبند الكبير يحرّك المرحلة أكثر من الصغير.",
    "What one person of this trade costs for one shift.": "ما يكلفه فرد واحد من هذه المهنة في وردية واحدة.",
    "What one unit really cost: total spend divided by the accepted quantity.":
        "ما كلفته الوحدة فعلاً: إجمالي المنصرف مقسوماً على الكمية المقبولة.",
    "What the client pays for the assigned quantity, less what the subcontractors charge for it.":
        "ما يدفعه العميل مقابل الكمية المسندة، ناقص ما يأخذه مقاولو الباطن عليها.",
    "What the client pays for these quantities, less what this subcontractor charges for them.":
        "ما يدفعه العميل مقابل هذه الكميات، ناقص ما يأخذه هذا المقاول عليها.",
    "What the client pays us for this quantity, less what the subcontractor charges for it.":
        "ما يدفعه لنا العميل مقابل هذه الكمية، ناقص ما يأخذه المقاول عليها.",
    "What the conditions booklet costs to buy from the client.": "قيمة شراء كراسة الشروط من العميل.",
    "What the item prices already carry for execution: the operating cost of every item times its quantity.":
        "ما يحمله تسعير البنود بالفعل للتنفيذ: تكلفة تشغيل كل بند مضروبة في كميته.",
    "What the quantity variance costs us at the item cost rate.": "ما يكلفنا فرق الكمية بتكلفة وحدة البند.",
    "What the subcontractors charge for the quantities assigned.": "ما يأخذه مقاولو الباطن مقابل الكميات المسندة.",
    "What the whole bill of quantities will cost once finished: assigned work at the subcontractors rates, the rest at our own cost rates.":
        "ما ستكلفه المقايسة كاملة عند انتهائها: الأعمال المسندة بأسعار مقاولي الباطن، والباقي بتكلفتنا.",
    "What this person costs the company in a month -- salary plus insurance and allowances. This is the figure spread over the projects they work on.":
        "ما يكلفه هذا الشخص للشركة في الشهر — الراتب زائد التأمينات والبدلات. هذا هو الرقم الذي يُوزَّع على المشاريع التي يعمل عليها.",
    "What we pay the subcontractor for one unit.": "ما ندفعه لمقاول الباطن مقابل الوحدة الواحدة.",
    "When the client opens the technical envelopes. Later than the submission deadline.":
        "موعد فتح العميل للمظاريف الفنية. لاحق لموعد التسليم.",
    "When the financial envelopes are opened and the award is decided.":
        "موعد فتح المظاريف المالية والبت في الترسية.",
    "Whether the technical office recommends bidding, and on what terms.":
        "هل يوصي المكتب الفني بالتقدم للمناقصة، وبأي شروط.",
    "Who owns the financial envelope and the bond for this tender.":
        "المسؤول عن المظروف المالي والتأمين في هذه المناقصة.",
    "Work accepted on work orders, valued at the item cost rates: what the work we did ourselves should have cost.":
        "الأعمال المقبولة في أوامر الشغل مقيَّمة بتكلفة وحدات البنود: ما كان يجب أن يكلفه ما نفّذناه بأنفسنا.",
    "Work completed on the bill of quantities that has not been put on a certificate to the client yet.":
        "الأعمال المنفَّذة من المقايسة والتي لم تُدرج بعد في مستخلص للعميل.",
    "Over Item Rate": "زيادة عن فئة البند",
    "The rate the bill of quantities item was priced on. What the job can afford to pay for one unit.":
        "الفئة التي سُعّر بند المقايسة على أساسها. ما يستطيع المشروع تحمّله للوحدة الواحدة.",
    "Quoted price less the item cost rate, per unit. A positive figure eats into the margin the item was priced with.":
        "السعر المعروض ناقص فئة تكلفة البند، للوحدة. الرقم الموجب يأكل من الهامش الذي سُعّر البند به.",
    "Approving %(approved)s of \"%(item)s\" is more than the %(requested)s the site asked for.":
        "اعتماد %(approved)s من \"%(item)s\" أكبر من %(requested)s التي طلبها الموقع.",
}
