from flask import Flask, request, jsonify
import requests
import csv
import os
from datetime import datetime

app = Flask(__name__)

@app.route("/", methods=["POST", "GET"])
def handle_webhook():
    if request.method == "GET":
        return jsonify({"status": "info", "message": "Ce service attend une requête POST."}), 200

    try:
        # Requête à l’API Gel des Avoirs
        url = 'https://gels-avoirs.dgtresor.gouv.fr/ApiPublic/api/v1/publication/derniere-publication-flux-json'
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"status": "error", "message": f"Erreur API {response.status_code}"}), 500

        data = response.json() if response.content else {}
        publications = data.get('Publications', {})
        date_publication = publications.get('DatePublication', None)
        publication_details = publications.get('PublicationDetail', [])

        filtered_data = []
        for publication in publication_details:
            filtered_publication = {
                'IdRegistre': publication.get('IdRegistre'),
                'Nom': publication.get('Nom'),
                'Prenom': None,
                'Date_de_naissance': None,
                'Alias': None,
                'Date_Publication': date_publication
            }

            for detail in publication.get('RegistreDetail', []):
                valeurs = detail.get('Valeur', [])
                if not valeurs:
                    continue
                v0 = valeurs[0]
                type_champ = detail.get('TypeChamp')
                if type_champ == 'PRENOM':
                    filtered_publication['Prenom'] = v0.get('Prenom')
                elif type_champ == 'DATE_DE_NAISSANCE':
                    filtered_publication['Date_de_naissance'] = f"{v0.get('Jour')}/{v0.get('Mois')}/{v0.get('Annee')}"
                elif type_champ == 'ALIAS':
                    filtered_publication['Alias'] = v0.get('Alias')

            filtered_data.append(filtered_publication)

        # ✅ Générer un nom de fichier basé sur la date de publication
        # Exemple API : "2025-08-16T00:00:00"
        pub_date_str = "inconnue"
        if date_publication:
            try:
                pub_date = datetime.fromisoformat(date_publication.replace("Z", ""))  
                pub_date_str = pub_date.strftime("%Y-%m-%d")
            except Exception:
                pub_date_str = date_publication.split("T")[0]  # fallback si mauvais format

        filename = f"gels_avoirs_{pub_date_str}.csv"
        filepath = os.path.join("/tmp", filename)

        # Écriture CSV
        fieldnames = ['IdRegistre', 'Nom', 'Prenom', 'Date_de_naissance', 'Alias', 'Date_Publication']
        with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(filtered_data)

        return jsonify({
            "status": "success",
            "message": f"CSV généré : {filename}",
            "path": filepath,
            "records_count": len(filtered_data)
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run()
