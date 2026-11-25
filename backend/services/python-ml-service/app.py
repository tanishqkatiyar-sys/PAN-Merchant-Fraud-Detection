
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask.json.provider import DefaultJSONProvider

import pandas as pd
import numpy as np
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from xgboost import XGBClassifier

import psycopg2
import os
import joblib
from dotenv import load_dotenv

load_dotenv()


# -------------------- JSON SERIALIZATION --------------------

class NumpyJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)

        if isinstance(obj, np.floating):
            return float(obj) if np.isfinite(obj) else None

        if isinstance(obj, np.ndarray):
            return obj.tolist()

        if isinstance(obj, np.bool_):
            return bool(obj)

        if obj is pd.NA:
            return None

        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()

        return super().default(obj)


app = Flask(__name__)
app.json = NumpyJSONProvider(app)
CORS(app)


# -------------------- CONFIGURATION --------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MERCHANT_CSV = os.getenv(
    "MERCHANT_CSV",
    "merchant_synthetic_100k.csv"
)

EDGE_CSV = os.getenv(
    "EDGE_CSV",
    "merchant_edges.csv"
)

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    os.path.join(BASE_DIR, "fraud_model.joblib")
)

PREDICTION_THRESHOLD = float(
    os.getenv("PREDICTION_THRESHOLD", "0.5")
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "fraud_detection"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

DROP_COLUMNS = [
    "merchant_registration_date",
    "merchant_age_days",
    "pan_hash",
    "device_id_hash",
    "ip_hash",
    "phone_hash",
    "pos_terminal_id_hash",
    "email_hash",
    "business_city",
    "city",
]

CATEGORICAL_COLUMNS = [
    "merchant_tier",
    "merchant_category"
]


# -------------------- GLOBAL VARIABLES --------------------

merchants_df = None
graph = nx.Graph()
fraud_rings = {}

embeddings_matrix = None
merchant_id_to_idx = {}

fraud_model = None
feature_columns = []
label_encoders = {}


# -------------------- CITY MAPPING --------------------

CITY_MAPPING = {
    "City_1": "Mumbai",
    "City_2": "Delhi",
    "City_3": "Bangalore",
    "City_4": "Hyderabad",
    "City_5": "Chennai",
    "City_6": "Kolkata",
    "City_7": "Pune",
    "City_8": "Ahmedabad",
    "City_9": "Surat",
    "City_10": "Jaipur",
    "City_11": "Lucknow",
    "City_12": "Kanpur",
    "City_13": "Nagpur",
    "City_14": "Indore",
    "City_15": "Thane",
    "City_16": "Bhopal",
    "City_17": "Visakhapatnam",
    "City_18": "Pimpri-Chinchwad",
    "City_19": "Patna",
    "City_20": "Vadodara",
    "City_21": "Ghaziabad",
    "City_22": "Ludhiana",
    "City_23": "Agra",
    "City_24": "Nashik",
    "City_25": "Faridabad",
    "City_26": "Meerut",
    "City_27": "Rajkot",
    "City_28": "Kalyan-Dombivali",
    "City_29": "Vasai-Virar",
    "City_30": "Varanasi",
    "City_31": "Srinagar",
    "City_32": "Aurangabad",
    "City_33": "Dhanbad",
    "City_34": "Amritsar",
    "City_35": "Navi Mumbai",
    "City_36": "Allahabad",
    "City_37": "Ranchi",
    "City_38": "Howrah",
    "City_39": "Coimbatore",
    "City_40": "Jabalpur",
    "City_41": "Gwalior",
    "City_42": "Vijayawada",
    "City_43": "Jodhpur",
    "City_44": "Madurai",
    "City_45": "Raipur",
    "City_46": "Kota",
    "City_47": "Chandigarh",
    "City_48": "Guwahati",
    "City_49": "Solapur",
    "City_50": "Hubli-Dharwad",
    "City_51": "Bareilly",
    "City_52": "Moradabad",
    "City_53": "Mysore",
    "City_54": "Tiruchirappalli",
    "City_55": "Tiruppur",
    "City_56": "Gurgaon",
    "City_57": "Aligarh",
    "City_58": "Jalandhar",
    "City_59": "Bhubaneswar",
    "City_60": "Salem",
    "City_61": "Warangal",
    "City_62": "Mira-Bhayandar",
    "City_63": "Thiruvananthapuram",
    "City_64": "Bhiwandi",
    "City_65": "Saharanpur",
    "City_66": "Gorakhpur",
    "City_67": "Guntur",
    "City_68": "Bikaner",
    "City_69": "Amravati",
    "City_70": "Noida",
    "City_71": "Jamshedpur",
    "City_72": "Bhilai",
    "City_73": "Cuttack",
    "City_74": "Firozabad",
    "City_75": "Vellore",
    "City_76": "Udaipur",
    "City_77": "Jhansi",
    "City_78": "Ulhasnagar",
    "City_79": "Siliguri",
    "City_80": "Dewas",
    "City_81": "Kurnool",
    "City_82": "Tumkur",
    "City_83": "Rohtak",
    "City_84": "Panipat",
    "City_85": "Darbhanga",
    "City_86": "Kozhikode",
    "City_87": "Akola",
    "City_88": "Belgaum",
    "City_89": "Kolhapur",
    "City_90": "Nanded",
    "City_91": "Ajmer",
    "City_92": "Gaya",
    "City_93": "Ujjain",
    "City_94": "Loni",
    "City_95": "Sagar",
    "City_96": "Rourkela",
    "City_97": "Anantapur",
    "City_98": "Bareja",
    "City_99": "Pondicherry",
    "City_100": "Bhavnagar",
    "City_101": "Haridwar",
    "City_102": "Nellore",
    "City_103": "Jammu",
    "City_104": "Muzaffarnagar",
    "City_105": "Malegaon",
    "City_106": "Bathinda",
    "City_107": "Tirupati",
    "City_108": "Hapur",
    "City_109": "Kakinada",
    "City_110": "Sirsa",
    "City_111": "Rewa",
    "City_112": "Satna",
    "City_113": "Ambala",
    "City_114": "Durgapur",
    "City_115": "Shimoga",
    "City_116": "Ratlam",
    "City_117": "Bardhaman",
    "City_118": "Bijapur",
    "City_119": "Sonipat",
    "City_120": "Unnao",
    "City_121": "Dehradun",
    "City_122": "Haldwani",
    "City_123": "Mirzapur",
    "City_124": "Bettiah",
    "City_125": "Motihari",
    "City_126": "Purnea",
    "City_127": "Jalgaon",
    "City_128": "Sangli",
    "City_129": "Chittoor",
    "City_130": "Ongole",
    "City_131": "Nizamabad",
    "City_132": "Karimnagar",
    "City_133": "Palakkad",
    "City_134": "Kollam",
    "City_135": "Mangalore",
    "City_136": "Bhagalpur",
    "City_137": "Hajipur",
    "City_138": "Muzaffarpur",
    "City_139": "Beed",
    "City_140": "Porbandar",
    "City_141": "Jalna",
    "City_142": "Chinsurah",
    "City_143": "Berhampur",
    "City_144": "Shillong",
    "City_145": "Aizawl",
    "City_146": "Imphal",
    "City_147": "Kohima",
    "City_148": "Agartala",
    "City_149": "Srinagar (Uttarakhand)",
    "City_150": "Itanagar",
    "City_151": "Etawah",
    "City_152": "Bulandshahr",
    "City_153": "Budaun",
    "City_154": "Alwar",
    "City_155": "Hoshiarpur",
    "City_156": "Maheshtala",
    "City_157": "Serampore",
    "City_158": "Kharagpur",
    "City_159": "Dibrugarh",
    "City_160": "Korba",
    "City_161": "Bilaspur",
    "City_162": "Gandhidham",
    "City_163": "Hingoli",
    "City_164": "Sambalpur",
    "City_165": "Shahjahanpur",
    "City_166": "Kota (Karnataka)",
    "City_167": "Rewari",
    "City_168": "Vidisha",
    "City_169": "Katni",
    "City_170": "Morbi",
    "City_171": "Surendranagar",
    "City_172": "Navsari",
    "City_173": "Gondia",
    "City_174": "Harda",
    "City_175": "Chhindwara",
    "City_176": "Damoh",
    "City_177": "Mandsaur",
    "City_178": "Neemuch",
    "City_179": "Sehore",
    "City_180": "Pali",
    "City_181": "Fatehpur",
    "City_182": "Raiganj",
    "City_183": "Jhunjhunu",
    "City_184": "Bharatpur",
    "City_185": "Sikar",
    "City_186": "Ganganagar",
    "City_187": "Banswara",
    "City_188": "Pratapgarh",
    "City_189": "Dausa",
    "City_190": "Barmer",
    "City_191": "Jalore",
    "City_192": "Churu",
    "City_193": "Nagaur",
    "City_194": "Koraput",
    "City_195": "Karaikal",
    "City_196": "Silchar",
    "City_197": "Tezpur",
    "City_198": "Nagaon",
    "City_199": "Balasore",
    "City_200": "Kendrapara"
}


# -------------------- DATABASE --------------------

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


# -------------------- GRAPH --------------------

def build_graph(edges_df):
    global graph

    graph = nx.Graph()

    if merchants_df is not None:
        graph.add_nodes_from(
            merchants_df["merchant_id"].astype(str)
        )

    if edges_df is None or edges_df.empty:
        return

    edges = edges_df.copy()
    edges.columns = [str(c).lower() for c in edges.columns]

    if not {"merchant_a", "merchant_b"}.issubset(edges.columns):
        print("Warning: edge table needs merchant_a and merchant_b.")
        return

    edges["merchant_a"] = edges["merchant_a"].astype(str).str.strip()
    edges["merchant_b"] = edges["merchant_b"].astype(str).str.strip()

    for _, row in edges.iterrows():
        a = row["merchant_a"]
        b = row["merchant_b"]

        if not a or not b or a == b:
            continue

        weight = 1.0
        reason = "unknown"

        if "weight" in edges.columns and pd.notna(row["weight"]):
            weight = float(row["weight"])

        if "reason" in edges.columns and pd.notna(row["reason"]):
            reason = str(row["reason"])

        graph.add_edge(
            a,
            b,
            weight=weight,
            reason=reason
        )

    print(
        f"Graph created: {graph.number_of_nodes()} nodes, "
        f"{graph.number_of_edges()} edges"
    )


def identify_fraud_rings():
    global fraud_rings

    fraud_rings = {}

    if merchants_df is None or "is_fraud" not in merchants_df.columns:
        return

    fraud_mask = (
        pd.to_numeric(merchants_df["is_fraud"], errors="coerce") == 1
    )

    fraud_ids = set(
        merchants_df.loc[fraud_mask, "merchant_id"].astype(str)
    )

    fraud_subgraph = graph.subgraph(fraud_ids).copy()

    for index, component in enumerate(
        nx.connected_components(fraud_subgraph)
    ):
        if len(component) >= 2:
            fraud_rings[f"ring_{index}"] = list(component)

    print(f"Identified {len(fraud_rings)} fraud rings.")


# -------------------- FEATURE PREPARATION --------------------

def prepare_training_features(data, fit_encoders=True):
    global feature_columns, label_encoders

    work = data.copy()

    work = work.drop(
        columns=DROP_COLUMNS,
        errors="ignore"
    )

    embedding_columns = [
        col for col in work.columns
        if str(col).startswith("emb_")
    ]

    work = work.drop(
        columns=embedding_columns,
        errors="ignore"
    )

    work = work.drop(
        columns=["is_fraud", "merchant_id"],
        errors="ignore"
    )

    # Encode categorical features.
    for col in CATEGORICAL_COLUMNS:

        if col not in work.columns:
            raise ValueError(
                f"Missing categorical column: {col}"
            )

        values = work[col].fillna("Unknown").astype(str)

        if fit_encoders:
            encoder = LabelEncoder()
            work[col] = encoder.fit_transform(values)

            label_encoders[col] = encoder

        else:
            encoder = label_encoders[col]

            known_classes = set(encoder.classes_)

            # Unknown categories use the reserved Unknown class
            # when it was present during training.
            values = values.where(
                values.isin(known_classes),
                "Unknown"
            )

            if "Unknown" not in known_classes and not values.isin(known_classes).all():
                raise ValueError(
                    f"Unknown category found in {col}. "
                    "Retrain the model with an Unknown category."
                )

            work[col] = encoder.transform(values)

    # Convert remaining columns to numeric.
    for col in work.columns:
        if not pd.api.types.is_numeric_dtype(work[col]):
            converted = pd.to_numeric(
                work[col],
                errors="coerce"
            )

            if converted.isna().any() and work[col].notna().any():
                raise ValueError(
                    f"Column '{col}' contains unsupported text values."
                )

            work[col] = converted

    work = work.replace(
        [np.inf, -np.inf],
        np.nan
    )

    if fit_encoders:
        numeric_medians = work.median(
            numeric_only=True
        ).to_dict()

        label_encoders["_numeric_medians"] = numeric_medians

    else:
        numeric_medians = label_encoders.get(
            "_numeric_medians",
            {}
        )

    work = work.fillna(numeric_medians)

    if work.isna().any().any():
        missing_columns = work.columns[
            work.isna().any()
        ].tolist()

        raise ValueError(
            f"Missing values could not be filled: {missing_columns}"
        )

    if fit_encoders:
        feature_columns = list(work.columns)

    else:
        missing = [
            col for col in feature_columns
            if col not in work.columns
        ]

        if missing:
            raise ValueError(
                f"Missing model features: {missing}"
            )

        work = work[feature_columns]

    return work.astype(float)


# -------------------- XGBOOST MODEL --------------------

def train_or_load_model():
    global fraud_model
    global feature_columns
    global label_encoders

    # Load previously trained model.
    if os.path.exists(MODEL_PATH):

        try:
            bundle = joblib.load(MODEL_PATH)

            fraud_model = bundle["model"]
            feature_columns = bundle["feature_columns"]
            label_encoders = bundle["label_encoders"]

            print(f"Loaded XGBoost model: {MODEL_PATH}")
            return

        except Exception as exc:
            print(f"Saved model could not be loaded: {exc}")
            print("Training a new model...")

    if merchants_df is None or "is_fraud" not in merchants_df.columns:
        raise RuntimeError(
            "Merchant dataset must contain is_fraud."
        )

    labels = pd.to_numeric(
        merchants_df["is_fraud"],
        errors="coerce"
    )

    valid_rows = (
        labels.notna()
        & labels.isin([0, 1])
    )

    training_data = merchants_df.loc[valid_rows].copy()
    y = labels.loc[valid_rows].astype(int)

    if y.nunique() != 2:
        raise RuntimeError(
            "Dataset must contain both fraud and legitimate merchants."
        )

    # Split before fitting preprocessing to avoid data leakage.
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        training_data,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y
    )

    # Fit preprocessing on training data only.
    X_train = prepare_training_features(
        X_train_raw,
        fit_encoders=True
    )

    X_test = prepare_training_features(
        X_test_raw,
        fit_encoders=False
    )

    fraud_ratio = float(y_train.mean())

    scale_pos_weight = (
        (1.0 - fraud_ratio) / fraud_ratio
        if fraud_ratio > 0
        else 1.0
    )

    fraud_model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.07,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        tree_method="hist",
        scale_pos_weight=scale_pos_weight,
        random_state=42
    )

    print("Training XGBoost model...")

    fraud_model.fit(
        X_train,
        y_train
    )

    # Evaluate on unseen test data.
    test_predictions = fraud_model.predict(X_test)

    test_accuracy = accuracy_score(
        y_test,
        test_predictions
    )

    print("\nXGBoost Test Accuracy:")
    print(f"{test_accuracy:.4f}")

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            test_predictions,
            zero_division=0
        )
    )

    # Save model and preprocessing configuration.
    os.makedirs(
        os.path.dirname(MODEL_PATH),
        exist_ok=True
    )

    joblib.dump(
        {
            "model": fraud_model,
            "feature_columns": feature_columns,
            "label_encoders": label_encoders
        },
        MODEL_PATH
    )

    print(f"Model saved: {MODEL_PATH}")


# -------------------- LOAD DATA --------------------

def load_data():
    global merchants_df
    global embeddings_matrix
    global merchant_id_to_idx

    try:
        print("Loading data from PostgreSQL...")

        conn = get_db_connection()

        try:
            merchants_df = pd.read_sql_query(
                "SELECT * FROM merchants",
                conn
            )

            edges_df = pd.read_sql_query(
                "SELECT * FROM merchant_edges",
                conn
            )

        finally:
            conn.close()

        print(
            f"Loaded {len(merchants_df)} merchants from PostgreSQL."
        )

    except Exception as exc:

        print(f"Database unavailable: {exc}")
        print("Loading CSV data...")

        merchant_path = MERCHANT_CSV
        edge_path = EDGE_CSV

        if not os.path.isabs(merchant_path):
            merchant_path = os.path.join(
                BASE_DIR,
                merchant_path
            )

        if not os.path.exists(merchant_path):

            fallback = os.path.join(
                BASE_DIR,
                "merchant_synthetic_100k_phase6.csv"
            )

            if os.path.exists(fallback):
                merchant_path = fallback

            else:
                raise FileNotFoundError(
                    f"Merchant CSV not found: {merchant_path}"
                )

        if not os.path.isabs(edge_path):
            edge_path = os.path.join(
                BASE_DIR,
                edge_path
            )

        merchants_df = pd.read_csv(
            merchant_path,
            dtype={"merchant_id": str}
        )

        edges_df = (
            pd.read_csv(edge_path)
            if os.path.exists(edge_path)
            else pd.DataFrame()
        )

        print(
            f"Loaded {len(merchants_df)} merchants from CSV."
        )

    if "merchant_id" not in merchants_df.columns:
        raise ValueError(
            "Dataset must contain merchant_id."
        )

    merchants_df["merchant_id"] = (
        merchants_df["merchant_id"]
        .astype(str)
        .str.strip()
    )

    if "business_city" in merchants_df.columns:
        merchants_df["city"] = (
            merchants_df["business_city"]
            .map(CITY_MAPPING)
            .fillna(merchants_df["business_city"])
        )

    elif "city" not in merchants_df.columns:
        merchants_df["city"] = "Unknown"

    # Load Node2Vec embeddings if present.
    embedding_cols = [
        f"emb_{i}" for i in range(16)
    ]

    if all(
        col in merchants_df.columns
        for col in embedding_cols
    ):

        embeddings_matrix = (
            merchants_df[embedding_cols]
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0)
            .to_numpy()
        )

        merchant_id_to_idx = {
            mid: idx
            for idx, mid in enumerate(
                merchants_df["merchant_id"].astype(str)
            )
        }

    else:
        embeddings_matrix = None
        merchant_id_to_idx = {}

        print(
            "Node2Vec embeddings not found. "
            "Similarity search disabled."
        )

    build_graph(edges_df)

    identify_fraud_rings()

    train_or_load_model()


# -------------------- XGBOOST PREDICTION --------------------

def make_prediction(merchant_record):

    if fraud_model is None:
        raise RuntimeError(
            "XGBoost model is not loaded."
        )

    row = pd.DataFrame([
        merchant_record
    ])

    X_new = prepare_training_features(
        row,
        fit_encoders=False
    )

    probabilities = fraud_model.predict_proba(
        X_new
    )[0]

    fraud_probability = float(probabilities[1])

    prediction = int(
        fraud_probability >= PREDICTION_THRESHOLD
    )

    return {
        "prediction": prediction,

        "prediction_label": (
            "Fraud"
            if prediction == 1
            else "Legitimate"
        ),

        "fraud_probability": round(
            fraud_probability,
            6
        ),

        "legitimate_probability": round(
            1.0 - fraud_probability,
            6
        ),

        "threshold": PREDICTION_THRESHOLD,

        "model": "XGBoost"
    }


# -------------------- HEALTH API --------------------

@app.route("/api/health", methods=["GET"])
def health_check():

    return jsonify({
        "status": "healthy",
        "service": "PAN Merchant Fraud Detection",
        "model_loaded": fraud_model is not None,
        "model": "XGBoost" if fraud_model is not None else None
    })


# -------------------- MODEL FEATURES API --------------------

@app.route("/api/model/features", methods=["GET"])
def get_model_features():

    return jsonify({
        "success": True,

        "required_features": feature_columns,

        "categorical_values": {
            col: label_encoders[col].classes_.tolist()
            for col in CATEGORICAL_COLUMNS
            if col in label_encoders
        }
    })


# -------------------- PREDICT NEW MERCHANT --------------------

@app.route("/api/predict", methods=["POST"])
def predict_new_merchant():

    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "success": False,
                "error": "Send a valid JSON object."
            }), 400

        missing = [
            col for col in feature_columns
            if col not in data
        ]

        if missing:
            return jsonify({
                "success": False,
                "error": "Missing required features.",
                "missing_fields": missing,
                "required_features": feature_columns
            }), 400

        result = make_prediction(data)

        result["success"] = True

        return jsonify(result)

    except ValueError as exc:

        return jsonify({
            "success": False,
            "error": str(exc)
        }), 400

    except Exception as exc:

        return jsonify({
            "success": False,
            "error": str(exc)
        }), 500


# -------------------- SIMILAR FRAUD MERCHANTS --------------------

def get_similar_frauds(merchant_id, top_n=10):

    if (
        embeddings_matrix is None
        or merchant_id not in merchant_id_to_idx
    ):
        return []

    if "is_fraud" not in merchants_df.columns:
        return []

    target_idx = merchant_id_to_idx[merchant_id]

    target_embedding = embeddings_matrix[
        target_idx:target_idx + 1
    ]

    fraud_mask = (
        pd.to_numeric(
            merchants_df["is_fraud"],
            errors="coerce"
        ) == 1
    )

    fraud_df = merchants_df.loc[
        fraud_mask
    ].copy()

    fraud_df = fraud_df[
        fraud_df["merchant_id"].astype(str) != str(merchant_id)
    ]

    fraud_df = fraud_df[
        fraud_df["merchant_id"].astype(str).isin(
            merchant_id_to_idx
        )
    ].copy()

    if fraud_df.empty:
        return []

    # Keep merchant rows and embedding indices aligned.
    indices = [
        merchant_id_to_idx[mid]
        for mid in fraud_df["merchant_id"].astype(str)
    ]

    similarities = cosine_similarity(
        target_embedding,
        embeddings_matrix[indices]
    )[0]

    fraud_df["similarity_score"] = similarities

    fraud_df = fraud_df.sort_values(
        "similarity_score",
        ascending=False
    ).head(top_n)

    results = []

    for _, row in fraud_df.iterrows():

        results.append({
            "merchant_id": str(row["merchant_id"]),

            "similarity_score": float(
                row["similarity_score"]
            ),

            "pan_hash": str(
                row.get("pan_hash", "")
            ),

            "merchant_tier": str(
                row.get("merchant_tier", "")
            ),

            "city": str(
                row.get("city", "Unknown")
            ),

            "avg_txn_value": safe_float(
                row.get("avg_txn_value", 0)
            ),

            "chargeback_rate": safe_float(
                row.get("chargeback_rate", 0)
            )
        })

    return results


def safe_float(value):

    try:
        result = float(value)

        if not np.isfinite(result):
            return 0.0

        return result

    except (TypeError, ValueError):
        return 0.0


# -------------------- TOP FRAUD RINGS --------------------

@app.route("/api/top-fraud-rings", methods=["GET"])
def get_top_fraud_rings():

    try:

        if not fraud_rings:
            return jsonify({
                "success": False,
                "error": "No fraud rings found."
            }), 404

        sorted_rings = sorted(
            fraud_rings.items(),
            key=lambda item: len(item[1]),
            reverse=True
        )[:10]

        rings_data = []

        for ring_id, members in sorted_rings:

            display_members = members[:100]

            nodes = []

            for merchant_id in display_members:

                rows = merchants_df[
                    merchants_df["merchant_id"] == merchant_id
                ]

                if rows.empty:
                    continue

                merchant = rows.iloc[0]

                nodes.append({
                    "id": merchant_id,
                    "merchant_id": merchant_id,

                    "pan_hash": str(
                        merchant.get("pan_hash", "")
                    ),

                    "merchant_tier": str(
                        merchant.get("merchant_tier", "")
                    ),

                    "city": str(
                        merchant.get("city", "Unknown")
                    ),

                    "is_fraud": int(
                        safe_float(
                            merchant.get("is_fraud", 1)
                        )
                    )
                })

            subgraph = graph.subgraph(
                display_members
            )

            edges = [
                {
                    "source": u,
                    "target": v,
                    "weight": safe_float(
                        data.get("weight", 1)
                    ),
                    "reason": str(
                        data.get("reason", "unknown")
                    )
                }

                for u, v, data in list(
                    subgraph.edges(data=True)
                )[:200]
            ]

            rings_data.append({

                "ring_id": ring_id,

                "size": len(members),

                "displayed_size": len(display_members),

                "is_truncated": (
                    len(members) > len(display_members)
                ),

                "members": display_members,

                "nodes": nodes,

                "edges": edges
            })

        return jsonify({
            "success": True,
            "rings": rings_data
        })

    except Exception as exc:

        return jsonify({
            "success": False,
            "error": str(exc)
        }), 500


# -------------------- MERCHANT DETAILS API --------------------

@app.route("/api/merchant/<merchant_id>", methods=["GET"])
def get_merchant_info(merchant_id):

    try:

        rows = merchants_df[
            merchants_df["merchant_id"] == str(merchant_id)
        ]

        if rows.empty:
            return jsonify({
                "success": False,
                "error": "Merchant not found"
            }), 404

        merchant = rows.iloc[0]

        # Existing label from PostgreSQL/dataset.
        actual_label = None

        if (
            "is_fraud" in merchant
            and pd.notna(merchant["is_fraud"])
        ):
            actual_label = int(
                merchant["is_fraud"]
            )

        result = {

            "success": True,

            "merchant": {

                "merchant_id": str(merchant_id),

                # DATABASE / DATASET LABEL
                "is_fraud": actual_label,

                "pan_hash": merchant.get("pan_hash"),

                "device_id_hash": merchant.get("device_id_hash"),

                "ip_hash": merchant.get("ip_hash"),

                "merchant_tier": merchant.get("merchant_tier"),

                "merchant_category": merchant.get("merchant_category"),

                "city": merchant.get("city", "Unknown"),

                "is_kyc_verified": merchant.get("is_kyc_verified"),

                "total_txns_90d": merchant.get("total_txns_90d"),

                "avg_txn_value": merchant.get("avg_txn_value"),

                "chargeback_rate": merchant.get("chargeback_rate"),

                "refund_ratio": merchant.get("refund_ratio"),

                "shared_pan_count": merchant.get("shared_pan_count"),

                "shared_device_count": merchant.get("shared_device_count"),

                "shared_ip_count": merchant.get("shared_ip_count")
            }
        }

        # XGBOOST MODEL PREDICTION
        try:

            result["model_prediction"] = make_prediction(
                merchant.to_dict()
            )

        except Exception as pred_error:

            result["prediction_warning"] = str(
                pred_error
            )

        # Existing graph-based fraud ring.
        if actual_label == 1:

            for ring_id, members in fraud_rings.items():

                if str(merchant_id) in members:

                    subgraph = graph.subgraph(
                        members
                    )

                    ring_nodes = []

                    for mid in members:

                        member_rows = merchants_df[
                            merchants_df["merchant_id"] == mid
                        ]

                        if member_rows.empty:
                            continue

                        member = member_rows.iloc[0]

                        ring_nodes.append({
                            "id": mid,
                            "merchant_id": mid,
                            "pan_hash": str(
                                member.get("pan_hash", "")
                            )
                        })

                    result["fraud_ring"] = {

                        "ring_id": ring_id,

                        "nodes": ring_nodes,

                        "edges": [
                            {
                                "source": u,
                                "target": v,
                                "weight": safe_float(
                                    data.get("weight", 1)
                                ),
                                "reason": str(
                                    data.get("reason", "unknown")
                                )
                            }

                            for u, v, data in subgraph.edges(
                                data=True
                            )
                        ]
                    }

                    break

            # Node2Vec similarity search.
            result["similar_frauds"] = get_similar_frauds(
                str(merchant_id),
                top_n=10
            )

        return jsonify(result)

    except Exception as exc:

        return jsonify({
            "success": False,
            "error": str(exc)
        }), 500


# -------------------- SEARCH API --------------------

@app.route("/api/search", methods=["POST"])
def search_merchant():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        merchant_id = str(
            data.get("merchant_id", "")
        ).strip()

        if not merchant_id:

            return jsonify({
                "success": False,
                "error": "Merchant ID is required"
            }), 400

        return get_merchant_info(
            merchant_id
        )

    except Exception as exc:

        return jsonify({
            "success": False,
            "error": str(exc)
        }), 500


# -------------------- START APPLICATION --------------------

if __name__ == "__main__":

    load_data()

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False
    )
