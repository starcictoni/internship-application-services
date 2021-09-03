#Examples of block kit templates BOT uses for conversations

def student_after_allocation_template(kompanija, ime_poslodavac, email_poslodavac, opis_posla):
    header = {"type":"header", "text": {
        "type":"plain_text",
        "text": "Alociran vam je poslodavac za praksu, sljedeći korak je da mu se javite mail-om kako bi ste dogovorili razgovor za praksu."
    }}
    
    fields_description =  {"type":"section", "text":{
        "type":"plain_text",
        "text": "Slijedi vam opis alociranog poslodavca:"
    }} 
    fields = {"type":"section", "fields":[
        {"type":"mrkdwn",
        "text":"*Kompanija:*\n"+kompanija},
        {"type":"mrkdwn",
        "text":"*Ime poslodavca:*\n"+ime_poslodavac},
        {"type":"mrkdwn",
        "text":"*Email poslodavca:*\n"+email_poslodavac},
        {"type":"mrkdwn",
        "text":"*Kratki opis posla:*\n"+opis_posla}
    ]}
    end_note = {"type":"section", "text":{
        "type":"plain_text",
        "text": "Sto prije posaljite mail poslodavcu kako bi ste započeli odrađivati stručnu praksu."
    }}
    
    end_end_note = {"type":"section", "text":{
        "type":"plain_text",
        "text": "Detaljan opis posla dogovarate s poslodavcem na razgovoru."
    }}
    #Finished sections
    sections_list = [header,fields_description,fields,end_note,end_end_note]
    return sections_list

def student_after_approval_template(instance, next_task):
    header = {
        "type":"header",
        "text":{
            "type":"plain_text",
            "text":"Čestitke!\nPoslodavac vas je odabrao da odradite praksu kod njega."
        }
    }

    section_one_text =  {"type":"section", "text":{
        "type":"plain_text",
        "text": "Jos je potrebno ispuniti podatke o tome kada planirate izvoditi praksu."
    }} 

    section_two_text =  {"type":"section", "text":{
        "type":"mrkdwn",
        "text": f"Molimo vas da popunite formu na http://bpmn.elaclo.com/form/{instance}/{next_task}"
    }} 
    #Finished section 
    sections_list = [header,section_one_text,section_two_text]
    return sections_list

def student_potvrda_template(instance, next_task):
    header = {
        "type":"header",
        "text":{
            "type":"plain_text",
            "text":"Zaprimljen je vaš odabir početka prakse."
        }
    }
    section_one_text = {
        "type":"section",
        "text":{
            "type":"mrkdwn",
            "text":"Kad *završite* s praksom, *dnevnik prakse* i *popunjenu potvrdu* predajte u formi."
        }
    }
    section_two_text = {
        "type":"section",
        "text":{
            "type":"mrkdwn",
            "text":f"Link za formu : http://bpmn.elaclo.com/form/{instance}/{next_task}"
        }
    }
    section_three_text = {
        "type":"section",
        "text":{
            "type":"plain_text",
            "text":"Sretno i uživajte na praksi :)"
        }
    }
    sections_list = [header, section_one_text, section_two_text, section_three_text]
    return sections_list

