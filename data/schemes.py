"""
Scheme knowledge base for RAG.
Two schemes: PM-KISAN and Ayushman Bharat.
Each scheme has eligibility rules, documents, and benefit info in both Hindi and English.
"""

SCHEMES = {
    "pm_kisan": {
        "id": "pm_kisan",
        "name_en": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        "name_hi": "पीएम-किसान (प्रधानमंत्री किसान सम्मान निधि)",
        "benefit_en": "₹6,000 per year (₹2,000 every 4 months) direct to bank account",
        "benefit_hi": "₹6,000 प्रति वर्ष (हर 4 महीने में ₹2,000) सीधे बैंक खाते में",
        "eligibility": {
            "occupation": ["farmer", "kisan", "किसान", "खेती"],
            "land_ownership": True,  # must own land
            "income_limit_en": "No income limit, but large landholders (>2 hectares in some states) may be excluded",
            "income_limit_hi": "कोई आय सीमा नहीं, लेकिन बड़े भूमि मालिक (कुछ राज्यों में 2 हेक्टेयर से अधिक) को छोड़ा जा सकता है",
            "excluded_en": "Government employees, income tax payers, professionals (doctors, lawyers, etc.)",
            "excluded_hi": "सरकारी कर्मचारी, आयकर दाता, पेशेवर (डॉक्टर, वकील आदि)",
        },
        "documents_en": [
            "Aadhaar Card",
            "Land ownership documents (Khasra/Khatauni)",
            "Bank account passbook (linked to Aadhaar)",
            "Mobile number linked to Aadhaar",
        ],
        "documents_hi": [
            "आधार कार्ड",
            "जमीन के कागजात (खसरा/खतौनी)",
            "बैंक पासबुक (आधार से जुड़ी)",
            "आधार से जुड़ा मोबाइल नंबर",
        ],
        "apply_en": "Apply at: pmkisan.gov.in OR visit nearest Common Service Centre (CSC) / Gram Panchayat",
        "apply_hi": "आवेदन करें: pmkisan.gov.in पर OR नजदीकी सामान्य सेवा केंद्र (CSC) / ग्राम पंचायत जाएं",
        "helpline": "PM-KISAN Helpline: 155261 / 1800115526",
        "keywords": ["farmer", "kisan", "farming", "agriculture", "land", "खेती", "किसान", "जमीन", "कृषि"],
    },

    "ayushman_bharat": {
        "id": "ayushman_bharat",
        "name_en": "Ayushman Bharat – PMJAY (Pradhan Mantri Jan Arogya Yojana)",
        "name_hi": "आयुष्मान भारत – पीएमजेएवाई (प्रधानमंत्री जन आरोग्य योजना)",
        "benefit_en": "₹5 lakh per year health insurance per family for secondary and tertiary hospitalisation",
        "benefit_hi": "परिवार के लिए प्रति वर्ष ₹5 लाख स्वास्थ्य बीमा (सरकारी व सूचीबद्ध अस्पतालों में)",
        "eligibility": {
            "income_limit_en": "Below Poverty Line (BPL) or SECC 2011 database listed families",
            "income_limit_hi": "गरीबी रेखा से नीचे (BPL) या SECC 2011 सूची में नाम",
            "categories_en": [
                "Families with no adult member aged 16-59",
                "Female-headed households",
                "Manual scavenging households",
                "Primitive tribal groups",
                "Legally released bonded labour",
                "Rural deprived households as per SECC",
            ],
            "categories_hi": [
                "ऐसे परिवार जिनमें 16-59 वर्ष का कोई सदस्य नहीं",
                "महिला मुखिया वाले परिवार",
                "हाथ से मैला उठाने वाले परिवार",
                "आदिम जनजाति समूह",
                "बंधुआ मजदूरी से मुक्त लोग",
                "SECC के अनुसार ग्रामीण वंचित परिवार",
            ],
        },
        "documents_en": [
            "Aadhaar Card (any family member)",
            "Ration Card",
            "Income Certificate (if applicable)",
            "Caste Certificate (if applicable for reserved categories)",
        ],
        "documents_hi": [
            "आधार कार्ड (परिवार के किसी भी सदस्य का)",
            "राशन कार्ड",
            "आय प्रमाण पत्र (यदि लागू हो)",
            "जाति प्रमाण पत्र (यदि आरक्षित श्रेणी के लिए)",
        ],
        "apply_en": "Check eligibility at: pmjay.gov.in OR call helpline. Visit nearest Ayushman Mitra at empanelled hospital.",
        "apply_hi": "पात्रता जांचें: pmjay.gov.in पर OR हेल्पलाइन कॉल करें। नजदीकी सूचीबद्ध अस्पताल में आयुष्मान मित्र से मिलें।",
        "helpline": "Ayushman Bharat Helpline: 14555 / 1800-111-565",
        "keywords": ["health", "hospital", "treatment", "medical", "illness", "sick", "insurance",
                     "स्वास्थ्य", "अस्पताल", "इलाज", "बीमारी", "बीमा", "दवाई"],
    },
}


ELIGIBILITY_QUESTIONS = {
    "en": [
        {
            "id": "occupation",
            "question": "What is your main occupation?\n1. Farmer (owns land)\n2. Daily wage / labour\n3. Small business\n4. Other",
            "options": ["1", "2", "3", "4"],
        },
        {
            "id": "ration_card",
            "question": "Do you have a ration card? (BPL/APL/Antyodaya)\n1. Yes, BPL/Antyodaya card\n2. Yes, APL card\n3. No ration card",
            "options": ["1", "2", "3"],
        },
        {
            "id": "family_income",
            "question": "What is your approximate monthly family income?\n1. Less than ₹5,000\n2. ₹5,000 – ₹15,000\n3. More than ₹15,000",
            "options": ["1", "2", "3"],
        },
        {
            "id": "aadhaar",
            "question": "Do you have an Aadhaar card?\n1. Yes\n2. No, but applied\n3. No",
            "options": ["1", "2", "3"],
        },
    ],
    "hi": [
        {
            "id": "occupation",
            "question": "आपका मुख्य काम क्या है?\n1. किसान (जमीन मालिक)\n2. मजदूर / दिहाड़ी\n3. छोटा व्यापार\n4. अन्य",
            "options": ["1", "2", "3", "4"],
        },
        {
            "id": "ration_card",
            "question": "क्या आपके पास राशन कार्ड है?\n1. हाँ, BPL/अंत्योदय कार्ड\n2. हाँ, APL कार्ड\n3. नहीं",
            "options": ["1", "2", "3"],
        },
        {
            "id": "family_income",
            "question": "आपके परिवार की मासिक आय लगभग कितनी है?\n1. ₹5,000 से कम\n2. ₹5,000 – ₹15,000\n3. ₹15,000 से अधिक",
            "options": ["1", "2", "3"],
        },
        {
            "id": "aadhaar",
            "question": "क्या आपके पास आधार कार्ड है?\n1. हाँ\n2. नहीं, आवेदन किया है\n3. नहीं",
            "options": ["1", "2", "3"],
        },
    ],
}