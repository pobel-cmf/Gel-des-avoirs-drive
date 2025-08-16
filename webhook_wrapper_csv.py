from flask import Flask, request, jsonify
import requests

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
                'Nature': publication.get('Nature'),
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

        # Retour JSON complet
        return jsonify({
            "status": "success",
            "records": filtered_data
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run()
