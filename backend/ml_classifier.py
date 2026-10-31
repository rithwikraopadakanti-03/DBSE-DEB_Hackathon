import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

class ComplaintClassifier:
    def __init__(self):
        self.category_pipeline = None
        self.priority_pipeline = None
        self.categories = [
            'Electrical',
            'Maintenance',
            'IT Support',
            'Hostel Administration',
            'Canteen',
            'Transport',
            'Academic',
            'Security'
        ]
        self._train()

    def _clean_text(self, text):
        if not text:
            return ""
        text = str(text).lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _train(self):
        # Comprehensive training dataset with 16 examples per category
        category_data = [
            # 1. Electrical
            ("Ceiling fan not working in room 302 making loud grinding noise then stopped", "Electrical"),
            ("Frequent power cuts in academic block B during study hours", "Electrical"),
            ("Tube light flickering and spark coming from the switchboard", "Electrical"),
            ("No electricity in laboratory 4 all wall plug sockets are completely dead", "Electrical"),
            ("Exhaust fan in hostel washroom burnt out and smelling like smoke", "Electrical"),
            ("Short circuit near water cooler in second floor corridor sparking heavily", "Electrical"),
            ("Street lights near boys hostel gate not functioning very dark at night", "Electrical"),
            ("Power outlet loose and sparking when phone or laptop charger is plugged in", "Electrical"),
            ("Air conditioner in seminar hall not cooling and tripping the circuit breaker", "Electrical"),
            ("Emergency lights on staircase not turning on during power outage", "Electrical"),
            ("Exposed electrical wires hanging from library ceiling hazardous for students", "Electrical"),
            ("Computer lab UPS constantly beeping and not holding backup power", "Electrical"),
            ("Switchboard burnt in chemistry lab after heavy voltage surge", "Electrical"),
            ("Water heater geyser in girls hostel bathroom not heating water", "Electrical"),
            ("Projector power cord damaged and sparking in lecture hall 101", "Electrical"),
            ("Main distribution board sparking near administrative office corridor", "Electrical"),

            # 2. Maintenance
            ("Water leakage from pipe in third floor washroom flooding the hallway", "Maintenance"),
            ("Broken window glass in classroom 204 dangerous for students", "Maintenance"),
            ("Door lock broken and latch jammed cannot lock room 115", "Maintenance"),
            ("Desk and wooden chairs damaged with exposed nails in lecture hall 3", "Maintenance"),
            ("Bathroom tap leaking continuously wasting huge amount of clean water", "Maintenance"),
            ("Wash basin drainage pipe choked and dirty water overflowing in hostel", "Maintenance"),
            ("Plaster falling from ceiling in mechanical engineering wing roof", "Maintenance"),
            ("Cracked floor tiles causing severe tripping hazard in main lobby entrance", "Maintenance"),
            ("Wooden bench broken in outdoor quadrangle area needs immediate repair", "Maintenance"),
            ("Roof leaking heavily during rain into library reading room books getting wet", "Maintenance"),
            ("Flush tank in hostel second floor toilet broken and not refilling water", "Maintenance"),
            ("Rusted iron railing on staircase loose and shaking when held", "Maintenance"),
            ("Window blinds torn and fallen down in departmental conference room", "Maintenance"),
            ("Door hinge broken door won't close or latch properly in faculty room", "Maintenance"),
            ("Drainage pipe blocked causing foul odor outside central mess hall", "Maintenance"),
            ("Severe seepage on classroom wall causing dampness and paint peeling off", "Maintenance"),

            # 3. IT Support
            ("Campus Wi-Fi not connecting in library reading area and computer lab", "IT Support"),
            ("Unable to access student portal and fee payment gateway error 500", "IT Support"),
            ("Computer in lab 3 blue screen crash when booting windows operating system", "IT Support"),
            ("Wi-Fi speeds extremely slow in hostel rooms cannot attend online classes", "IT Support"),
            ("Cannot connect to college ERP system login authentication failed repeatedly", "IT Support"),
            ("Ethernet port in research lab not getting IP address DHCP network failure", "IT Support"),
            ("Network printer in department office offline and print queue stuck", "IT Support"),
            ("Forgot college email password cannot reset through verification link", "IT Support"),
            ("Smart classroom projector display resolution distorted and screen flickering", "IT Support"),
            ("Virtual learning management system LMS not loading course assignment materials", "IT Support"),
            ("Software license expired for MATLAB and CAD software in engineering lab", "IT Support"),
            ("Hostel Wi-Fi access point router keeps rebooting every ten minutes", "IT Support"),
            ("Campus intranet portal inaccessible from student personal laptops", "IT Support"),
            ("Lab desktop keyboard and optical mouse not detected by system", "IT Support"),
            ("Biometric attendance machine failing to read student fingerprint scanner", "IT Support"),
            ("Network switch failure in computer center entire row disconnected from internet", "IT Support"),

            # 4. Hostel Administration
            ("Room allocation issue roommates allotted incorrectly in block C hostel", "Hostel Administration"),
            ("Hostel warden not responding to room shifting request submitted last month", "Hostel Administration"),
            ("Excessive noise and loud music during quiet study hours in wing B hostel", "Hostel Administration"),
            ("Hostel laundry washing machines out of order since last two weeks", "Hostel Administration"),
            ("Hostel room keys lost need duplicate key from chief warden office", "Hostel Administration"),
            ("Pest infestation bed bugs and cockroaches in hostel room 210", "Hostel Administration"),
            ("Water supply timing not adhered to no running water in morning hours", "Hostel Administration"),
            ("Night curfew and hostel gate pass permission system taking too long to approve", "Hostel Administration"),
            ("Drinking water dispenser empty in hostel floor 4 no fresh refill done", "Hostel Administration"),
            ("Hostel common room TV and recreational indoor games equipment broken", "Hostel Administration"),
            ("Unauthorized visitors entering hostel premises without entry log at gate", "Hostel Administration"),
            ("Cleaning staff not sweeping or mopping hostel corridors on regular schedule", "Hostel Administration"),
            ("Cooler water stagnant mosquito breeding observed in hostel inner courtyard", "Hostel Administration"),
            ("Request for medical isolation room due to infectious viral fever outbreak", "Hostel Administration"),
            ("Hostel fee receipt discrepancy in warden office accounts records", "Hostel Administration"),
            ("Mattress and curtains provided in hostel room in torn and dirty condition", "Hostel Administration"),

            # 5. Canteen
            ("Unhygienic food served in canteen hair found in cooked meal", "Canteen"),
            ("Stale and spoiled food served in cafeteria causing food poisoning symptoms", "Canteen"),
            ("Canteen drinking water filter dirty and water smells foul", "Canteen"),
            ("Canteen staff not wearing gloves hairnets or masks while handling food", "Canteen"),
            ("Overcharging students above printed MRP for packaged food items and beverages", "Canteen"),
            ("Mess food quality extremely poor rice uncooked and dal watery without salt", "Canteen"),
            ("Cockroaches spotted near food serving counter in main college canteen", "Canteen"),
            ("Lack of healthy meal options and fresh fruits in campus mess dining", "Canteen"),
            ("Dirty utensils and metal trays not washed properly with hot water detergent", "Canteen"),
            ("Expired dairy products and sour milk sold at campus cafeteria counter", "Canteen"),
            ("Canteen tables and seating greasy covered with food spills and not wiped down", "Canteen"),
            ("Mess weekly food menu not followed and food quantity running out too early", "Canteen"),
            ("Food served cold and tasteless in engineering hostel mess", "Canteen"),
            ("Flies and insects hovering over open uncovered food trays in cafeteria", "Canteen"),
            ("Canteen vendor refusing digital payments and demanding extra cash surcharge", "Canteen"),
            ("Bad burnt oil smell and cooking oil reused repeatedly for deep frying snacks", "Canteen"),

            # 6. Transport
            ("College bus route 14 arriving 45 minutes late every morning at pickup stop", "Transport"),
            ("Bus driver driving rashly and over speeding near busy highway crossing", "Transport"),
            ("College bus overcrowded students forced to stand on footboard dangerously", "Transport"),
            ("Bus pass RFID verification scanner malfunctioning causes long boarding delay", "Transport"),
            ("College bus broke down halfway on the road no alternate transport arranged", "Transport"),
            ("Evening return bus leaving 20 minutes before scheduled departure time", "Transport"),
            ("Seat cushions torn and bus interior very dirty and dusty with trash", "Transport"),
            ("Campus shuttle service not stopping at designated student pickup stops", "Transport"),
            ("Bus air conditioning not working in scorching summer afternoon commute", "Transport"),
            ("Transport fee paid online but physical bus pass sticker not issued by office", "Transport"),
            ("Emergency door in college bus route 5 jammed and cannot open in crisis", "Transport"),
            ("No college bus service available for weekend extra classes and laboratory", "Transport"),
            ("Bus route 8 altered without prior notice leaving students stranded at stop", "Transport"),
            ("Reckless driving and mobile phone usage while driving by college van driver", "Transport"),
            ("Bicycle parking shed near gate 2 lacks roof and bicycle locking rails", "Transport"),
            ("Two wheeler parking lot overcrowded and student motorcycles getting scratched", "Transport"),

            # 7. Academic
            ("Course syllabus not completed before mid semester examinations start", "Academic"),
            ("Semester grade sheet contains severe error in marks calculation for CS301", "Academic"),
            ("Faculty member not conducting scheduled tutorial and lab practical sessions", "Academic"),
            ("Discrepancy in attendance calculation marked absent while physically present", "Academic"),
            ("Course registration portal bug preventing elective course selection and save", "Academic"),
            ("Unreasonable delay in evaluation and return of midterm examination answer sheets", "Academic"),
            ("Timetable clash between two mandatory departmental core courses", "Academic"),
            ("Lack of prescribed reference textbooks and research journals in departmental library", "Academic"),
            ("Lab equipment inadequate for 60 students per batch in physics laboratory", "Academic"),
            ("Final year project guide assignment dispute and lack of faculty mentorship", "Academic"),
            ("Exam question paper had out of syllabus questions for 25 marks", "Academic"),
            ("Grade dispute in final project presentation evaluation rubric", "Academic"),
            ("Request for paper re-evaluation and marks recounting not processed on time", "Academic"),
            ("Continuous internal assessment marks not displayed before final examinations", "Academic"),
            ("Faculty member absent without substitute arrangement for past two weeks", "Academic"),
            ("Classroom microphone not audible in large auditorium lecture theater", "Academic"),

            # 8. Security
            ("Theft of laptop and backpack from library second floor study cubicle", "Security"),
            ("Suspicious trespassers roaming near girls hostel boundary wall after dark", "Security"),
            ("CCTV camera outside parking lot facing wrong direction or completely dead", "Security"),
            ("Security guard sleeping on duty at main campus gate at midnight", "Security"),
            ("Bicycle stolen from bicycle stand despite parking token being issued", "Security"),
            ("Harassment incident near college back gate in poorly lit pathway", "Security"),
            ("Physical altercation and fighting between outsider group and students on campus", "Security"),
            ("Security gate boom barricade broken vehicles entering without vehicle checking", "Security"),
            ("Lost wallet and student identification card in sports complex ground", "Security"),
            ("Unauthorized entry into mechanical engineering workshop after closing hours", "Security"),
            ("Aggressive stray dogs inside campus attacking students at night near cafeteria", "Security"),
            ("Emergency SOS alarm button near athletic track not responding when pressed", "Security"),
            ("Night campus security patrol missing in dimly lit perimeter walkway", "Security"),
            ("Intruder climbed over low broken boundary fence near sports pavilion", "Security"),
            ("Fire extinguisher expired and safety pin broken in science block hallway", "Security"),
            ("Security staff behaving rudely and refusing to log visitor identity details", "Security")
        ]

        # Priority training data (Critical, High, Medium, Low)
        priority_data = [
            # Critical (immediate safety hazard, fire, smoke, violence, injury, entrapment)
            ("Fire and thick smoke coming from electrical panel near classroom 201", "Critical"),
            ("Short circuit causing huge sparks and burning smell in boys hostel wing", "Critical"),
            ("Exposed live electrical high voltage wire hanging over water puddle in pathway", "Critical"),
            ("Ceiling plaster and concrete slabs collapsing over students desks in chemistry lab", "Critical"),
            ("Severe food poisoning 15 students vomiting and rushed to hospital from mess", "Critical"),
            ("Intruder with sharp weapon spotted near girls hostel boundary wall", "Critical"),
            ("Violent physical assault and bloody fight outside main campus gate", "Critical"),
            ("Elevator lift stuck with 6 students trapped inside between 3rd and 4th floors", "Critical"),
            ("LPG gas cylinder leaking gas odor in central canteen kitchen", "Critical"),
            ("Aggressive rabid dog biting students in campus quadrangle walkway", "Critical"),
            ("Toxic chemical spill and noxious fumes spreading in chemistry laboratory", "Critical"),
            ("Main transformer exploding and caught fire near electrical substation", "Critical"),
            ("Emergency exit doors padlocked and completely blocked during safety drill", "Critical"),
            ("Student collapsed unconscious in auditorium no medical response team", "Critical"),
            ("College bus brake failed on highway slope barely avoided major accident", "Critical"),

            # High (major disruption, flooding, security breach, severe system outages)
            ("Water main burst flooding the entire 3rd floor corridor and classrooms", "High"),
            ("Entire hostel block has total power outage for 8 hours before semester exam", "High"),
            ("College exam portal crashed 30 minutes before final project submission deadline", "High"),
            ("Theft of research laptop with unbacked dissertation from locked laboratory", "High"),
            ("No running water or drinking water in entire girls hostel building all day", "High"),
            ("Stale contaminated food served causing widespread nausea and stomach pain", "High"),
            ("Hostel washroom drainage backing up with raw sewage overflowing into hallway", "High"),
            ("Broken window glass with large sharp shards dangling directly over student seats", "High"),
            ("Suspicious unknown individuals wandering inside hostel corridors at 2 AM", "High"),
            ("Campus core server down during final semester subject registration window", "High"),
            ("Bus driver driving recklessly on the wrong side of the road at high speed", "High"),
            ("Fire extinguisher empty or missing in computer server room", "High"),
            ("Rusted iron staircase railing detached and hanging dangerously over drop", "High"),
            ("Biometric entrance gates locked and student crowd crushed at entrance", "High"),
            ("Discrepancy in final graduation degree marks preventing job joining", "High"),

            # Medium (moderate disruption, broken equipment, routine maintenance, delays)
            ("Ceiling fan making loud squeaking noise and vibrating in room 204", "Medium"),
            ("Classroom projector flickering display during faculty lecture presentations", "Medium"),
            ("College bus route 12 arriving 30 minutes late consistently every morning", "Medium"),
            ("Hostel Wi-Fi signal weak and dropping connection repeatedly during evening", "Medium"),
            ("Washroom tap dripping continuously wasting water in block A", "Medium"),
            ("Attendance calculation discrepancy on student portal for two lectures", "Medium"),
            ("Canteen food quality subpar and served lukewarm today", "Medium"),
            ("Hostel room door lock loose needs screwdriver repair and tightening", "Medium"),
            ("One tube light not turning on in quiet study room", "Medium"),
            ("LMS portal very slow when downloading lecture PDF slides", "Medium"),
            ("Departmental printer jammed and out of toner cartridge", "Medium"),
            ("Washing machine in hostel laundry vibrating violently during spin cycle", "Medium"),
            ("Bicycle parking stand congested and token counter unattended", "Medium"),
            ("Library desk wooden edge chipped causing student clothes to snag", "Medium"),
            ("AC cooling in seminar hall inadequate for large crowd", "Medium"),

            # Low (minor cosmetic, small inconvenience, suggestions, non-urgent)
            ("Request for additional whiteboard markers and dusters in classroom 102", "Low"),
            ("Notice board glass has fingerprint smudges and needs cleaning", "Low"),
            ("Curtains in faculty lounge need washing and ironing", "Low"),
            ("Paint peeling slightly on outdoor corridor boundary wall", "Low"),
            ("Suggestion to include fresh fruit salad in afternoon canteen menu", "Low"),
            ("Bicycle parking painted boundary lines slightly faded on road", "Low"),
            ("Wall clock in library reading room running 5 minutes slow", "Low"),
            ("Small surface scratch on conference room wooden podium", "Low"),
            ("Request to renew subscription for technology magazines in reading hall", "Low"),
            ("Water dispenser paper cup dispenser empty near reception", "Low"),
            ("Minor spelling mistake on departmental website faculty profile page", "Low"),
            ("Request to place an additional dustbin near football ground bench", "Low"),
            ("Classroom podium microphone foam cover missing", "Low"),
            ("Air freshener needed in administrative floor reception lounge", "Low"),
            ("Request for updating bulletin board with upcoming club events calendar", "Low")
        ]

        # Prepare Category Training
        cat_texts = [self._clean_text(item[0]) for item in category_data]
        cat_labels = [item[1] for item in category_data]

        self.category_pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=3500, sublinear_tf=True)),
            ('clf', LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced'))
        ])
        self.category_pipeline.fit(cat_texts, cat_labels)

        # Prepare Priority Training
        prio_texts = [self._clean_text(item[0]) for item in priority_data]
        prio_labels = [item[1] for item in priority_data]

        self.priority_pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=2500, sublinear_tf=True)),
            ('clf', LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced'))
        ])
        self.priority_pipeline.fit(prio_texts, prio_labels)

    def predict_category(self, title, description):
        """
        Return top 3 category predictions with confidence scores.
        """
        combined = f"{title or ''} {description or ''}".strip()
        cleaned = self._clean_text(combined)

        if not cleaned or self.category_pipeline is None:
            # Fallback if no text provided
            return [
                {"category": self.categories[0], "confidence": 0.40},
                {"category": self.categories[1], "confidence": 0.30},
                {"category": self.categories[2], "confidence": 0.30}
            ]

        probs = self.category_pipeline.predict_proba([cleaned])[0]
        classes = self.category_pipeline.classes_
        top_indices = np.argsort(probs)[::-1][:3]

        return [
            {
                "category": str(classes[idx]),
                "confidence": round(float(probs[idx]), 4)
            }
            for idx in top_indices
        ]

    def predict_priority(self, title, description, category=None):
        """
        Return predicted priority: Low, Medium, High, Critical.
        Combines model inference with critical keyword safety overrides.
        """
        combined = f"{title or ''} {description or ''}".strip()
        cleaned = self._clean_text(combined)

        if not cleaned:
            return "Medium"

        # Explicit safety keywords for Critical level
        critical_keywords = [
            r'\bfire\b', r'\bsmoke\b', r'\bspark\b', r'\bsparking\b',
            r'\bshort circuit\b', r'\belectrocute\b', r'\belectric shock\b',
            r'\bexplosion\b', r'\bcollapsing\b', r'\bcollapse\b',
            r'\bpoison\b', r'\bpoisoning\b', r'\btrapped\b', r'\bweapon\b',
            r'\bassault\b', r'\bintruder\b', r'\bgas leak\b', r'\bbleeding\b',
            r'\bunconscious\b', r'\brabid\b'
        ]
        for pattern in critical_keywords:
            if re.search(pattern, cleaned):
                return "Critical"

        # Explicit high priority keywords
        high_keywords = [
            r'\bflooding\b', r'\bpipe burst\b', r'\bno electricity\b',
            r'\btheft\b', r'\bstolen\b', r'\bexam portal\b', r'\bserver down\b',
            r'\braw sewage\b', r'\bbroken glass\b', r'\bno water\b'
        ]
        for pattern in high_keywords:
            if re.search(pattern, cleaned):
                return "High"

        # Fallback to ML priority pipeline
        if self.priority_pipeline is not None:
            predicted = self.priority_pipeline.predict([cleaned])[0]
            return str(predicted)

        return "Medium"

    def get_recommendations(self, title, description):
        """
        Return dict with category_predictions and predicted priority.
        """
        category_predictions = self.predict_category(title, description)
        top_category = category_predictions[0]["category"] if category_predictions else None
        priority = self.predict_priority(title, description, category=top_category)

        return {
            "category_predictions": category_predictions,
            "priority": priority
        }

# Singleton instance for application-wide use
classifier = ComplaintClassifier()
