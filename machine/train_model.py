"""train_model.py
-----------------
Script to train and save the KNN sport recommender model.
This script handles the training pipeline: load data from database, 
train the model, and save it to disk for production use.
"""

from ml_knn_recommender import KNNSportRecommender

def train_and_save_model():
    """Train the KNN recommender and save it for production use"""
    print("\n" + "="*60)
    print("KNN SPORT RECOMMENDER - MODEL TRAINING")
    print("="*60 + "\n")
    
    # Create and train recommender
    recommender = KNNSportRecommender(n_neighbors=10)  # Create a new recommender that finds 10 similar sports
    recommender.load_and_train()  # Load data from database and train the model
    
    # Save the model (prepare for production deployment)
    print("\n" + "="*60)  # Print visual separator to distinguish model saving section
    recommender.save_model("knn_recommender.joblib")  # Persist complete trained model bundle to disk for instant loading in production Streamlit app
    print("✅ KNN ML Model ready for production!")  # Confirm successful model training and saving - ready for integration with web application
    print("="*60 + "\n")  # Print closing visual separator for clean console output

if __name__ == "__main__":
    train_and_save_model()