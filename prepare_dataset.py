
import json
import os
import pandas as pd
from datasets import Dataset, DatasetDict, load_dataset

# ============================================
# 1. LOAD YOUR INDIA-SPECIFIC DATA
# ============================================
india_medical_data = [
{
"instruction": "Patient: I have been coughing for 3 weeks and sometimes spit blood.",
"response": "Doctor: Any cough over 2 weeks in India requires a TB workup. We need a Chest X-ray and a sputum test (CBNAAT/GeneXpert) to rule out Tuberculosis. Is there anyone else in the family with TB?"
},
{
"instruction": "Patient: I was diagnosed with TB. My urine has turned orange-red after starting the medicines.",
"response": "Doctor: Do not worry. The orange-red urine is a harmless side effect of Rifampicin, one of the main drugs in your AKT-4 kit. Continue the medication; do not stop."
},
{
"instruction": "Patient: My child has asthma. Is it safe to use inhalers? People say they are addictive.",
"response": "Doctor: That is a common myth in India. Inhalers deliver medicine directly to the lungs and are the safest, most effective treatment for Asthma. They are not addictive. We will start with a Metered Dose Inhaler (MDI) with a spacer."
},
{
"instruction": "Patient: I work in a stone crushing unit and have breathlessness.",
"response": "Doctor: Occupational history suggests Silicosis. We need a Chest X-ray to look for egg-shell calcification. There is no cure, but we must prevent complications like TB, which is very common in silicosis patients."
},
{
"instruction": "Patient: I have a gland swelling in my neck that is matted and painless.",
"response": "Doctor: In India, Scrofula (Tuberculous Lymphadenitis) is a very common cause of neck swellings. We need an FNAC (Needle test) to check for AFB (Acid Fast Bacilli) or Granulomas. If positive, you will need 6 months of anti-TB treatment."
},
{
"instruction": "Patient: I have severe pollution in my city (Delhi). I have a constant cough in winter.",
"response": "Doctor: This is likely Smoker's cough or Pollution-induced Bronchitis/COPD. Wear an N95 mask outdoors. We may need to start you on a bronchodilator (Levosalbutamol) and check your PFT (Lung function test)."
},
{
"instruction": "Patient: Can I stop my TB meds now? I feel fine after 2 months.",
"response": "Doctor: Absolutely not. You have completed the Intensive Phase, but you must complete the Continuation Phase (total 6 months). Stopping now will cause MDR-TB (Multi-Drug Resistant TB), which is much harder to treat."
},
{
"instruction": "Patient: I have a cough and difficulty breathing. My oxygen saturation is 92%.",
"response": "Doctor: Given the post-COVID context, we must rule out pneumonia. Get a HRCT Chest. If saturation drops below 94%, we advise admission or oxygen support. Start proning (lying on stomach) to improve oxygenation."
},
{
"instruction": "Patient: I am taking AKT-4. My eyes are looking yellow.",
"response": "Doctor: Jaundice (Hepatotoxicity) is a known side effect of TB drugs (Isoniazid, Rifampicin, Pyrazinamide). Stop the medicines immediately and get an LFT done. We will modify the regimen once the liver heals."
},
{
"instruction": "Patient: I have fever and a sore throat. It hurts to swallow.",
"response": "Doctor: Likely Acute Pharyngitis. In India, we check if it's Streptococcal. Gargle with warm salt water or Betadine gargles. Take Azithromycin 500mg for 3 days if bacterial infection is suspected."
},
{
"instruction": "Patient: I have high fever, severe joint pain, and cannot walk properly for 2 days.",
"response": "Doctor: The severe joint pain (arthralgia) with fever strongly suggests Chikungunya. It is viral. We need to manage pain with Paracetamol (Dolo 650) and hydrate. Avoid NSAIDs until dengue is ruled out. Rest is crucial as joint pain can persist."
},
{
"instruction": "Patient: I found a black scab on my skin after returning from a trekking trip in Himachal. I have fever now.",
"response": "Doctor: That black scab is likely an 'Eschar', which is pathognomonic for Scrub Typhus (Mite typhus). Given the travel history and fever, we should start Doxycycline immediately and send a sample for IgM ELISA for Scrub Typhus."
},
{
"instruction": "Patient: I have fever with chills and rigors coming every alternate day.",
"response": "Doctor: Fever with chills and rigors is a classic sign of Malaria. In India, we see both Vivax and Falciparum strains. We need a Peripheral Blood Smear (PBS) and Rapid Antigen Test. If positive, we will start ACT (Artemisinin-based Combination Therapy) or Chloroquine based on the strain."
},
{
"instruction": "Patient: I waded through flood water in Mumbai last week. Now I have fever, red eyes, and calf pain.",
"response": "Doctor: This triad of history (flood water contact), conjunctival suffusion (red eyes), and calf tenderness suggests Leptospirosis. We must treat this aggressively with Doxycycline or Penicillin to prevent renal complications. Get a Urine RE and Creatinine test done."
},
{
"instruction": "Patient: My child has had fever for 5 days and now has a 'strawberry' tongue and peeling skin on hands.",
"response": "Doctor: We need to investigate for Kawasaki Disease, which is increasingly diagnosed in India. However, we must first rule out Scarlet Fever. An ECHO is mandatory to check coronary arteries. Immediate hospitalization is required."
},
{
"instruction": "Patient: I have a painless ulcer on my genital area. I am worried.",
"response": "Doctor: In the Indian context, a painless genital ulcer (chancre) is the primary sign of Syphilis. We need a VDRL or RPR test. If positive, a shot of Benzathine Penicillin G is the standard treatment."
},
{
"instruction": "Patient: Dog bit me on the leg. It was a stray dog.",
"response": "Doctor: Wash the wound with soap and water for 15 minutes immediately. Since it is a stray dog (unknown vaccination status), this is a Category III exposure if there is any blood. You need the Rabies Vaccine (0, 3, 7, 14, 28 days schedule) and Rabies Immunoglobulin (RIG) infiltrated around the wound."
},
{
"instruction": "Patient: I have loose motions, 'rice-water' like stools, and severe dehydration.",
"response": "Doctor: Rice-water stools are the hallmark of Cholera. This is an emergency. You need rapid rehydration. If you can drink, take ORS continuously. If not, we need to start IV fluids (Ringer Lactate) immediately. Doxycycline helps reduce the duration."
},
{
"instruction": "Patient: I have fever for 2 weeks. Widal test shows TO 1:160 and TH 1:320.",
"response": "Doctor: While Widal is common in India, it can have false positives. However, these titres with 2 weeks of fever suggest Enteric Fever (Typhoid). We should start antibiotics like Cefixime or Azithromycin. Ensure you drink only boiled water."
},
{
"instruction": "Patient: I have a ring-shaped itchy patch on my groin.",
"response": "Doctor: This is Tinea Cruris (Jock Itch), very common in India's humid climate. Do not use steroid creams (like Betnovate) as they worsen it. Use an antifungal cream like Luliconazole or Clotrimazole for 4 weeks and keep the area dry."
},
{
"instruction": "Patient: I am a vegetarian. I feel tired and have tingling in my feet.",
"response": "Doctor: This is classic Vitamin B12 deficiency, prevalent in Indian vegetarians. We will start you on Methylcobalamin supplements. Also, check your Vitamin D levels, as deficiency is common here despite the sun."
},
{
"instruction": "Patient: I have diabetes. Can I eat Mangoes and Rice?",
"response": "Doctor: You can, but in moderation. Mango implies a high glycemic load. If you eat mango, reduce your portion of rice (carbohydrates) for that meal to balance the sugar. Brown rice or Chapati is preferred over white rice."
},
{
"instruction": "Patient: My Haemoglobin is 8.0 g/dL. I feel dizzy.",
"response": "Doctor: You have moderate Anemia. In India, Iron Deficiency is the most common cause. Start Ferrous Ascorbate tablets. Include jaggery, spinach, and dates in your diet. Avoid drinking tea/coffee immediately after meals as it blocks iron absorption."
},
{
"instruction": "Patient: My father has chest pain after climbing stairs. He chews tobacco.",
"response": "Doctor: Tobacco chewing is a major risk factor for Coronary Artery Disease in India. The symptoms suggest Angina. Put a Sorbitrate tablet under his tongue if pain recurs and get an ECG and TMT (Treadmill Test) done immediately."
},
{
"instruction": "Patient: I have darker skin on my neck and armpits.",
"response": "Doctor: This is Acanthosis Nigricans, a sign of Insulin Resistance. It is a warning sign for Type 2 Diabetes. We need to check your HbA1c and fasting insulin. Weight loss and Metformin usually help."
},
{
"instruction": "Patient: I have high BP. The doctor gave me 'Amlodipine'. My feet are swelling.",
"response": "Doctor: Ankle edema (swelling) is a common side effect of Amlodipine. It is not dangerous but can be bothersome. Keep your feet elevated. If it persists, we can switch you to Telmisartan or another class of antihypertensive."
},
{
"instruction": "Patient: I want to gain weight. I am very thin.",
"response": "Doctor: First, we deworm with Albendazole to rule out worm infestation. Then, increase calorie intake with healthy fats like Ghee, nuts, and bananas. Ensure you don't have Hyperthyroidism (check TSH)."
},
{
"instruction": "Patient: I have burning sensation in my chest (Heartburn).",
"response": "Doctor: GERD is common with spicy Indian food. Avoid lying down immediately after dinner. You can take a PPI like Pantoprazole (Pantop-D) empty stomach in the morning for 2 weeks. Avoid tea and spicy curries."
},
{
"instruction": "Patient: My sugar levels are 250 fasting. I am on Glycomet 500.",
"response": "Doctor: Your diabetes is uncontrolled. We need to escalate treatment. We may add a Sulfonylurea (like Glimepiride) or a DPP4 inhibitor (like Teneligliptin) to your Metformin. Please follow a strict diabetic diet."
},
{
"instruction": "Patient: I have a small stone in my kidney (4mm).",
"response": "Doctor: 4mm stones usually pass with hydration. Drink 3-4 liters of water daily. You can take Cystone syrup (Ayurvedic support) or Tamsulosin to help passage. Avoid tomatoes and spinach if it's an oxalate stone."
},
{
"instruction": "Patient: My child drank some kerosene by mistake.",
"response": "Doctor: Do NOT induce vomiting, as this can cause aspiration pneumonia (chemical pneumonitis). Rush to the ER. We will observe the child for breathing difficulties. Chest X-ray may be needed after 6 hours."
},
{
"instruction": "Patient: I have severe acidity. Can I take Eno?",
"response": "Doctor: Eno provides temporary relief but has high sodium content. If you have high blood pressure, avoid it. For frequent acidity, use a liquid antacid like Digene or Gelusil, or a PPI like Omeprazole."
},
{
"instruction": "Patient: I have a headache. Can I take Combiflam?",
"response": "Doctor: Combiflam contains Ibuprofen and Paracetamol. It is effective, but avoid it if you have a history of acidity or dengue (as NSAIDs increase bleeding risk). For simple headache, plain Paracetamol (Crocin/Dolo) is safer."
},
{
"instruction": "Patient: Farmer patient: He sprayed pesticides and now has pin-point pupils and excessive salivation.",
"response": "Doctor: This is classic Organophosphorus (OP) Poisoning. It is a medical emergency. Administer Atropine IV immediately until signs of atropinization (dilated pupils, dry mouth) appear. Pralidoxime (PAM) may also be needed."
},
{
"instruction": "Patient: Which calcium tablet is best for pregnancy?",
"response": "Doctor: In government setups, we provide Calcium Carbonate + Vitamin D3 (Shelcal is a common brand). Take it after lunch. Do not take it with your Iron tablet, as calcium blocks iron absorption."
},
{
"instruction": "Patient: My wound is not healing. Can I put turmeric on it?",
"response": "Doctor: While turmeric has antiseptic properties, putting raw powder on open wounds can introduce infection or tetanus spores. Please use medical ointment like Betadine (Povidone Iodine) or Neosporin. Keep the wound covered."
},
{
"instruction": "Patient: I have a UTI. The chemist gave me Norflox.",
"response": "Doctor: Norfloxacin is a standard first-line antibiotic for UTI in India. Ensure you drink plenty of water (urine should be clear). Complete the 3 or 5-day course even if symptoms stop. Add a Urine Alkalizer (Cital) for burning relief."
},
{
"instruction": "Patient: I am taking oral contraceptive pills (Mala-D). I missed one pill yesterday.",
"response": "Doctor: Take the missed pill as soon as you remember, even if it means taking two pills today. Continue the rest of the pack as usual. Mala-D is a standard government supply pill."
},
{
"instruction": "Patient: I have hair fall. I am using Minoxidil.",
"response": "Doctor: Minoxidil is FDA approved. Be aware of the 'shedding phase' in the first month where hair fall increases. This is normal. Continued use for 6 months is needed for visible results. You can add Biotin supplements."
},
{
"instruction": "Patient: My child has worms. What to give?",
"response": "Doctor: For deworming, we give Albendazole 400mg as a single dose (chewable tablet). Repeat after 2 weeks if infestation is heavy. In India, National Deworming Day is observed to cover this prophylactically."
},
{
"instruction": "Patient: My newborn has yellow eyes. It is day 3 of birth.",
"response": "Doctor: Physiological Jaundice is common on Day 3. Keep the baby well-hydrated with breast milk. If the yellowness extends to the palms or soles, we need to check Serum Bilirubin to see if Phototherapy is required."
},
{
"instruction": "Patient: I am pregnant. My feet swell in the evening.",
"response": "Doctor: Mild pedal edema is normal in pregnancy due to pressure. However, we must check your Blood Pressure and Urine Albumin to rule out Pre-eclampsia. Sleep on your left side to improve circulation."
},
{
"instruction": "Patient: Can I give my 4-month-old baby water?",
"response": "Doctor: No. As per WHO and Indian guidelines, exclusive breastfeeding is recommended for the first 6 months. No water, no honey, no gripe water. Breast milk has enough water even for Indian summers."
},
{
"instruction": "Patient: I have white discharge with itching.",
"response": "Doctor: This sounds like Candidiasis (Yeast infection). It is common in humid weather. We prescribe a Clotrimazole vaginal pessary (tablet to insert) and an antifungal cream. maintain hygiene and keep the area dry."
},
{
"instruction": "Patient: My periods are irregular and I have acne. I have gained weight.",
"response": "Doctor: This triad points towards PCOS (Polycystic Ovarian Syndrome). We need an Ultrasound and hormonal profile. Lifestyle modification (weight loss) is the first line of treatment, not just medicines."
},
{
"instruction": "Patient: My child is not eating anything. (Loss of appetite)",
"response": "Doctor: In India, 'poor appetite' is a common complaint. Rule out Iron deficiency and constipation first. Do not force-feed. Give nutrient-dense foods like Khichdi with ghee, rather than biscuits or milk alone."
},
{
"instruction": "Patient: When should I give the Measles vaccine?",
"response": "Doctor: Under the Universal Immunization Programme (UIP), the first dose of MR (Measles-Rubella) is given at 9 months completed, and the second dose at 15 months."
},
{
"instruction": "Patient: I have severe pain during periods (Dysmenorrhea).",
"response": "Doctor: You can take Mefenamic Acid (Meftal-Spas) for pain relief. It is safe. Using a hot water bag helps. If pain is worsening every month, we might need an ultrasound to check for Endometriosis."
},
{
"instruction": "Patient: I had a C-section. When can I start household work?",
"response": "Doctor: You can do light activities immediately. Avoid heavy lifting (like heavy buckets of water) for 6 weeks. Walking is encouraged to prevent clots."
},
{
"instruction": "Patient: My child has diarrhea. Should I stop milk?",
"response": "Doctor: Do not stop breastfeeding. If the child is on top milk (cow/buffalo), you can dilute it slightly or switch to lactose-free formula temporarily if diarrhea persists. Zinc syrup 20mg for 14 days is mandatory."
},
{
"instruction": "Patient: I want to know the gender of my unborn baby.",
"response": "Doctor: I cannot disclose that. Under the PCPNDT Act in India, sex determination is a criminal offense for both the doctor and the parents. It is strictly illegal to ask or tell."
},
{
"instruction": "Patient: I am 22 weeks pregnant and want an abortion.",
"response": "Doctor: Under the MTP Amendment Act 2021, termination is allowed up to 24 weeks for special categories (like survivors of sexual assault, minors, or fetal anomalies). We need a medical board opinion if it is beyond 20 weeks."
},
{
"instruction": "Patient: I was assaulted. I need a medical checkup.",
"response": "Doctor: We will provide immediate care. As per protocol, we must document all injuries in the MLC (Medico-Legal Case) register. You are entitled to free treatment. We will also collect evidence if you consent."
},
{
"instruction": "Patient: My relative died at home. We need a death certificate.",
"response": "Doctor: If the patient was under my treatment, I can issue a Cause of Death certificate. If it was a sudden, unexplained death, you must inform the police for a post-mortem to get the official certificate."
},
{
"instruction": "Patient: Do I need a prescription for sleeping pills?",
"response": "Doctor: Yes. Sedatives and anxiolytics (like Alprazolam/Nitrazepam) are Schedule H1 drugs in India. They cannot be sold without a valid, stamped prescription from a registered medical practitioner."
},
{
"instruction": "Patient: Doctor, mujhe 3 din se high fever hai aur thand lag rahi hai. (I have high fever and feeling cold for 3 days)",
"response": "Doctor: Fever with 'thand' (chills) often indicates Malaria or viral fever. Are you having shivering (kapkapi)? We should get a Malaria parasite test and CBC done."
},
{
"instruction": "Patient: Sir, mere pet me bahut tez dard ho raha hai right side me. (Sir, I have severe pain in my stomach on the right side)",
"response": "Doctor: Right-sided stomach pain (pet dard) can be Appendicitis or Kidney stones. Is the pain shifting from the navel? Any vomiting? We need an Ultrasound Abdomen immediately."
},
{
"instruction": "Patient: Bachhe ko kal raat se loose motions ho rahe hain. (Child has loose motions since last night)",
"response": "Doctor: Keep the child hydrated. Give ORS sip-by-sip immediately. Does the motion look watery or is there blood? If it's watery, start Zinc syrup along with ORS. Avoid antibiotics unless prescribed."
},
{
"instruction": "Patient: Doctor, mujhe saans lene me takleef ho rahi hai. (Doctor, I am having trouble breathing)",
"response": "Doctor: 'Saans lene me takleef' (Dyspnea) is serious. Check your oxygen saturation with a pulse oximeter. Do you have a history of Asthma or heart issues? If it's sudden, visit the ER."
},
{
"instruction": "Patient: Mere gale me kharash hai aur dry cough hai. (I have a scratchy throat and dry cough)",
"response": "Doctor: For 'gale me kharash' (sore throat), try warm saline gargles. You can take a lozenge like Strepsils. If the cough persists for more than 2 weeks, we must rule out TB."
},
{
"instruction": "Patient: Mera sar ghum raha hai (chakkar aa rahe hain) jab mai khada hota hu. (My head is spinning/dizzy when I stand up)",
"response": "Doctor: 'Chakkar' (Dizziness) on standing suggests Postural Hypotension (low BP). Drink plenty of water with salt. Check your BP lying down and standing up."
},
{
"instruction": "Patient: Body me bahut weakness feel ho rahi hai. Kuch khane ka mann nahi karta. (Feeling very weak in body. Don't feel like eating)",
"response": "Doctor: Loss of appetite and weakness are general symptoms. Look for pallor (pale eyes) for Anemia. Ensure you are eating frequent small meals. Get a CBC and LFT done."
},
{
"instruction": "Patient: Doctor, skin par laal daane (rash) nikal aaye hain. (Doctor, red rashes have appeared on skin)",
"response": "Doctor: Are these 'laal daane' itchy? If they are localized, it could be an allergy. If they are all over the body with fever, it could be Measles or Dengue. Avoid scratching."
},
{
"instruction": "Patient: Mere pairon me sujan aa gayi hai. (Swelling has come in my feet)",
"response": "Doctor: 'Pairon me sujan' (Pedal Edema) can be due to anemia, kidney, or heart issues. Are you diabetic? We need to check your Urine Albumin and Creatinine."
},
{
"instruction": "Patient: Seene me jalan ho rahi hai khana khane ke baad. (Burning in chest after eating)",
"response": "Doctor: This is Acidity or Heartburn. Avoid spicy food ('masaledar khana'). Take an antacid gel like Digene. Do not lie down immediately after dinner."
},
{
"instruction": "Patient: Doctor, peshab me jalan ho rahi hai. (Burning sensation in urine)",
"response": "Doctor: 'Peshab me jalan' is a sign of UTI. Drink 3-4 liters of water. Start a Urine Alkalizer (like Cital syrup) in water. If fever comes, we need antibiotics."
},
{
"instruction": "Patient: Mujhe raat ko neend nahi aati. (I don't get sleep at night)",
"response": "Doctor: Insomnia can be due to stress. Practice sleep hygiene—no phone 1 hour before bed. Try drinking warm milk. Do not start sleeping pills without a prescription."
},
{
"instruction": "Patient: Doctor, mere ghutno me dard rehta hai. (Doctor, pain remains in my knees)",
"response": "Doctor: 'Ghutno me dard' in older age is likely Osteoarthritis. Avoid sitting cross-legged on the floor. Use a western toilet. Physiotherapy for quadriceps strengthening helps."
},
{
"instruction": "Patient: Mujhe 2 mahine se period nahi aaya. (I haven't got my period for 2 months)",
"response": "Doctor: First, do a UPT (Urine Pregnancy Test) at home using a kit like Prega News. If negative, it could be hormonal imbalance or PCOS."
},
{
"instruction": "Patient: Bachhe ke kaan me dard hai. (Child has pain in ear)",
"response": "Doctor: Ear pain in children is often Otitis Media. Do not put oil in the ear. Give Paracetamol for pain. If there is discharge, seeing an ENT is mandatory."
},
{
"instruction": "Patient: Mere muh me chhale ho gaye hain. (I have ulcers in my mouth)",
"response": "Doctor: Mouth ulcers ('chhale') are often due to vitamin deficiency or stomach heat. Take B-Complex (Bikasul) capsules and apply an oral gel like Dolo-Gel."
},
{
"instruction": "Patient: Doctor, kutte ne kaat liya. (Doctor, a dog bit me)",
"response": "Doctor: Clean the wound with soap and water for 15 minutes immediately. Visit the hospital for the Anti-Rabies Vaccine. Do not apply chili or turmeric to the wound."
},
{
"instruction": "Patient: Mere baal bahut jhad rahe hain. (My hair is falling a lot)",
"response": "Doctor: Hair fall can be due to stress, thyroid, or iron deficiency. Use a mild shampoo. We can check Ferritin and TSH levels."
},
{
"instruction": "Patient: Aankhen laal ho gayi hain aur chiphak rahi hain. (Eyes have turned red and are sticking)",
"response": "Doctor: This looks like Conjunctivitis ('Aankh aana'). It is contagious. Wash hands frequently. Use antibiotic eye drops like Moxifloxacin. Isolate your towel."
},
{
"instruction": "Patient: Doctor, meri kamar me dard hai. (Doctor, I have back pain)",
"response": "Doctor: Back pain is common. Use a hard mattress. Avoid bending forward to lift weights. Apply Volini spray and take rest. If pain goes down the leg, it might be Sciatica."
},
{
"instruction": "Patient: Mera wazan kam ho raha hai bina koshish kiye. (My weight is reducing without trying)",
"response": "Doctor: Unexplained weight loss is a red flag. In India, we rule out Tuberculosis (TB) and Diabetes first. Please get a chest X-ray and sugar test."
},
{
"instruction": "Patient: Mujhe thoda thoda bukhar rehta hai sham ko. (I have mild fever in the evenings)",
"response": "Doctor: Evening rise of temperature is a classic sign of Tuberculosis. Do you also sweat at night? We need to investigate this thoroughly."
},
{
"instruction": "Patient: Skin par safed daag dikh raha hai. (White patch is visible on skin)",
"response": "Doctor: A white patch ('safed daag') could be Vitiligo or a fungal infection. If it is not itchy and losing sensation, we check for leprosy as well."
},
{
"instruction": "Patient: Doctor, mujhe gas bahut banti hai. (Doctor, I get a lot of gas)",
"response": "Doctor: Avoid tea, coffee, and pulses (dal) at night. Walk for 15 minutes after meals. You can take a probiotic to improve digestion."
},
{
"instruction": "Patient: Mere daant me dard hai. (I have toothache)",
"response": "Doctor: Rinse with warm salt water. Take a painkiller like Ketorolac (Ketorol-DT). Visit a dentist to check for cavities or infection."
},


{
"instruction": "Patient: A snake bit my brother in the farm. We don't know which snake. He is drowsy.",
"response": "Doctor: This is a medical emergency. Keep the patient still; do NOT cut or suck the wound. Immobilize the limb. Rush to a hospital that has Polyvalent Anti-Snake Venom (ASV). Drowsiness (ptosis) suggests a Neurotoxic bite (Cobra/Krait)."
},
{
"instruction": "Patient: I was bitten by a snake. The site is swelling rapidly and bleeding is not stopping.",
"response": "Doctor: Rapid swelling and bleeding abnormalities suggest a Hemotoxic bite (Viper). You need ASV immediately. We will monitor Whole Blood Clotting Time (WBCT-20) to assess venom neutralization."
},


{
"instruction": "Patient: I have fever and a cigarette-burn like mark on my groin.",
"response": "Doctor: That mark is an 'Eschar'. It is highly specific for Scrub Typhus. We will start Doxycycline 100mg twice a day for 7 days. This usually resolves the fever quickly."
},


{
"instruction": "Patient: I cannot open my mouth fully. I have been chewing Gutka for 10 years.",
"response": "Doctor: Restricted mouth opening is a sign of Oral Submucous Fibrosis (OSMF), a pre-cancerous condition. Stop Gutka immediately. We need to start antioxidant therapy and intralesional steroids. A biopsy may be needed to rule out malignancy."
},
{
"instruction": "Patient: I have a white patch in my mouth that cannot be scraped off.",
"response": "Doctor: This is likely Leukoplakia. Given the risk of oral cancer in India, we must biopsy this lesion. Avoid tobacco and sharp teeth irritation."
},


{
"instruction": "Patient: My neck looks swollen in the front. I have difficulty swallowing.",
"response": "Doctor: This appears to be a Goiter (Thyroid swelling). We need a USG Neck and Thyroid Profile (T3, T4, TSH). We will also check if it's simple iodine deficiency or autoimmune."
},


{
"instruction": "Patient: The normal TB medicines are not working. My fever is back.",
"response": "Doctor: We suspect Drug-Resistant TB (MDR-TB). We need to send a sample for Line Probe Assay (LPA) and Culture/DST. Do not restart the old medicines; we may need to switch to a Bedaquiline-based regimen."
},


{
"instruction": "Patient: My platelet count is 80,000. Do I need a transfusion?",
"response": "Doctor: No. In Dengue, prophylactic platelet transfusion is not needed unless counts drop below 10,000 or there is active bleeding. We monitor the Hematocrit (PCV) more closely than platelets to check for plasma leakage."
},


{
"instruction": "Patient: I feel anxious and my heart beats fast before exams.",
"response": "Doctor: Exam anxiety is common in students. Try deep breathing exercises (Pranayama). If palpitations are severe, we can consider a short course of Beta-blockers like Propranolol, but only after an ECG."
},
{
"instruction": "Patient: My grandfather forgets names and gets lost in the house.",
"response": "Doctor: Progressive memory loss in the elderly suggests Dementia or Alzheimer's. We need a specific MRI of the brain. Ensure his safety at home to prevent falls."
},
{
"instruction": "Patient: I feel sad and don't want to talk to anyone. I lost my job.",
"response": "Doctor: I understand this is a tough time. Persistent low mood for 2 weeks suggests Clinical Depression. We can start Counseling. If needed, SSRIs like Sertraline are safe and non-addictive."
},
{
"instruction": "Patient: My knee replacement surgery was suggested. Is it safe?",
"response": "Doctor: Total Knee Replacement (TKR) is a standard and safe procedure in India now. Since you have severe Osteoarthritis and limited mobility, it will improve your quality of life significantly."
},
{
"instruction": "Patient: I want to quit chewing tobacco/Gutka.",
"response": "Doctor: That is a great decision. We can use Nicotine Replacement Therapy (NRT) like gums or patches (Nicotex). We can also use Bupropion to reduce cravings."
}
]


# ============================================
# 2. LOAD HUGGINGFACE DATASET
# ============================================
print("Loading HuggingFace medical chatbot dataset...")
hf_dataset = load_dataset("ruslanmv/ai-medical-chatbot", split="train")

def format_hf(example):
    patient = example.get('Patient', example.get('input', example.get('question', '')))
    doctor = example.get('Doctor', example.get('output', example.get('answer', '')))
    return {
        "instruction": f"Patient: {patient}",
        "response": f"Doctor: {doctor}"
    }

hf_formatted = hf_dataset.map(format_hf)
hf_list = [{"instruction": item["instruction"], "response": item["response"]} 
           for item in hf_formatted]

print(f"✅ Loaded {len(hf_list)} examples from HuggingFace")

# ============================================
# 3. LOAD CHATDOCTOR JSON FILES
# ============================================
print("\nLoading ChatDoctor datasets...")
chatdoctor_data = []

# HealthCareMagic-100k.json
if os.path.exists("HealthCareMagic-100k.json"):
    print("📂 Found HealthCareMagic-100k.json")
    with open("HealthCareMagic-100k.json", 'r', encoding='utf-8') as f:
        healthcare_magic = json.load(f)
        
        for item in healthcare_magic:
            patient_query = item.get('input', '').strip()
            doctor_response = item.get('output', '').strip()
            
            if patient_query and doctor_response:
                chatdoctor_data.append({
                    "instruction": f"Patient: {patient_query}",
                    "response": f"Doctor: {doctor_response}"
                })
    
    print(f"   ✅ Loaded {len(chatdoctor_data)} examples from HealthCareMagic")

# iCliniq.json
icliniq_start = len(chatdoctor_data)
if os.path.exists("iCliniq.json"):
    print("📂 Found iCliniq.json")
    with open("iCliniq.json", 'r', encoding='utf-8') as f:
        icliniq_data = json.load(f)
        
        for item in icliniq_data:
            patient_query = item.get('input', '').strip()
            doctor_response = (
                item.get('answer_icliniq', '') or 
                item.get('answer_chatdoctor', '') or 
                item.get('answer_chatgpt', '')
            ).strip()
            
            if patient_query and doctor_response:
                chatdoctor_data.append({
                    "instruction": f"Patient: {patient_query}",
                    "response": f"Doctor: {doctor_response}"
                })
    
    print(f"   ✅ Loaded {len(chatdoctor_data) - icliniq_start} examples from iCliniq")

if not chatdoctor_data:
    print("⚠️  ChatDoctor files not found. Proceeding without them.")
else:
    print(f"\n✅ Total ChatDoctor examples: {len(chatdoctor_data)}")

# ============================================
# 4. ADD MENTAL HEALTH CONVERSATIONAL DATA
# ============================================
mental_health_data = [
    {
        "instruction": "Patient: I feel very stressed about my studies. Can we just talk?",
        "response": "Doctor: Of course. I'm here to listen. What's been weighing on your mind the most? Is it exam pressure, or something else?"
    },
    {
        "instruction": "Patient: I don't know... everything feels overwhelming.",
        "response": "Doctor: I understand. Sometimes it helps to break things down. Can you tell me what happened recently that made you feel this way?"
    },
    {
        "instruction": "Patient: My parents fight a lot. It makes me sad.",
        "response": "Doctor: That sounds really difficult. It's natural to feel sad when people we love are in conflict. Have you been able to talk to someone you trust about this?"
    },
    {
        "instruction": "Patient: No one understands. Everyone says 'you'll be fine'.",
        "response": "Doctor: I hear you. Sometimes people don't know how to respond, but that doesn't mean your feelings aren't valid. You're not alone in this. Let's work through it together."
    },
    {
        "instruction": "Patient: Can you just tell me a joke? I need to laugh.",
        "response": "Doctor: Of course! Here's one: Why did the doctor carry a red pen? In case they needed to draw blood! 😊 How are you feeling right now?"
    },
    {
        "instruction": "Patient: I'm scared about my health reports.",
        "response": "Doctor: It's completely normal to feel anxious while waiting for results. Let's take it one step at a time. Whatever the results, we will handle it together. Would you like to talk about what specifically worries you?"
    },
    {
        "instruction": "Patient: I can't sleep at night. Too many thoughts.",
        "response": "Doctor: Racing thoughts at night are exhausting. Have you tried the 4-7-8 breathing technique? Breathe in for 4 seconds, hold for 7, exhale for 8. It calms the mind. Would you like to try it now?"
    },
    {
        "instruction": "Patient: I miss my grandmother. She passed away last month.",
        "response": "Doctor: I'm so sorry for your loss. Grief is a heavy burden, and there's no timeline for healing. It's okay to miss her. Would you like to share a memory of her that makes you smile?"
    },
    {
        "instruction": "Patient: Doctor, do you think I'm being dramatic?",
        "response": "Doctor: Not at all. Your feelings are real and important. If something is bothering you, it deserves attention. I'm here to support you, not to judge."
    },
    {
        "instruction": "Patient: Thank you for listening. I feel a bit better.",
        "response": "Doctor: I'm glad I could help. Remember, it's okay to reach out anytime you need someone to talk to. You're doing great by seeking support. Take care of yourself. 😊"
    }
]

# ============================================
# 5. COMBINE ALL DATASETS
# ============================================
all_data = india_medical_data + mental_health_data + chatdoctor_data + hf_list

print(f"\n{'='*60}")
print(f"📊 FINAL DATASET STATISTICS")
print(f"{'='*60}")
print(f"   India-specific examples:      {len(india_medical_data):>10,}")
print(f"   Mental health examples:       {len(mental_health_data):>10,}")
print(f"   ChatDoctor examples:          {len(chatdoctor_data):>10,}")
print(f"   HuggingFace examples:         {len(hf_list):>10,}")
print(f"   {'─'*60}")
print(f"   TOTAL TRAINING EXAMPLES:      {len(all_data):>10,}")
print(f"{'='*60}\n")

# ============================================
# 6. FORMAT FOR BIOMISTRAL (INSTRUCTION TUNING)
# ============================================
def format_for_biomistral(example):
    """
    Formats data in BioMistral's instruction format with:
    - System prompt defining AgentFoundry's personality
    - Patient query
    - Doctor response
    """
    system_prompt = """You are AgentFoundry, an empathetic AI medical assistant for India.

Your role:
- Provide clear, accurate medical guidance
- Ask clarifying questions when diagnosis is unclear
- Show empathy and emotional support
- Use simple language (accessible to patients with low medical literacy)
- Recommend doctor visits for serious symptoms
- Support mental health conversations
- Understand Indian medical context (diseases, medications, cultural practices)
- Respond in the patient's language (English, Hindi, Hinglish)

Remember: You are a supportive companion, not just a diagnostic tool."""

    prompt = f"""<s>[INST] {system_prompt}

{example['instruction']} [/INST]
{example['response']}</s>"""
    
    return {"text": prompt}

# Apply formatting
print("🔄 Formatting dataset for BioMistral training...")
formatted_data = [format_for_biomistral(item) for item in all_data]

# ============================================
# 7. CREATE HUGGINGFACE DATASET
# ============================================
print("💾 Creating HuggingFace Dataset...")
final_dataset = Dataset.from_dict({"text": [item["text"] for item in formatted_data]})

# Split into train/validation (90/10)
print("✂️  Splitting into train/validation (90/10)...")
train_test_split = final_dataset.train_test_split(test_size=0.1, seed=42)

dataset_dict = DatasetDict({
    "train": train_test_split["train"],
    "validation": train_test_split["test"]
})

# Save to disk
print("💾 Saving to disk...")
dataset_dict.save_to_disk("./agentfoundry_dataset")

print("\n✅ Dataset prepared and saved to ./agentfoundry_dataset")
print(f"   Training examples:   {len(dataset_dict['train']):>10,}")
print(f"   Validation examples: {len(dataset_dict['validation']):>10,}")

# ============================================
# 8. PREVIEW SAMPLES
# ============================================
print("\n" + "="*60)
print("📊 SAMPLE TRAINING EXAMPLES")
print("="*60)

for i in range(3):
    print(f"\n{'─'*60}")
    print(f"EXAMPLE {i+1}")
    print(f"{'─'*60}")
    sample_text = dataset_dict["train"][i]["text"]
    
    if "[INST]" in sample_text and "[/INST]" in sample_text:
        parts = sample_text.split("[/INST]")
        instruction_part = parts[0].split("[INST]")[1].strip()
        response_part = parts[1].replace("</s>", "").strip()
        
        patient_query = instruction_part.split("\n")[-1].strip()
        
        print(f"🗣️  {patient_query}")
        print(f"\n🤖 Doctor: {response_part[:300]}{'...' if len(response_part) > 300 else ''}")

print("\n" + "="*60)
print("🎯 Dataset is READY for training!")
print("="*60)
print("\n🚀 Next step: python train_agentfoundry.py")
print("⏰ Estimated training time: 10-14 hours on RTX 4060")
print("💡 TIP: Start it now and let it run overnight!\n")
