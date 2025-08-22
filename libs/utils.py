class Utils:
    @staticmethod
    def map_genres(genre: str):
        lower_genre = str(genre).lower()
        if "r&b" in lower_genre:
            return "R&B"
        elif "pop" in lower_genre:
            return "Pop"
        elif "rap" in lower_genre or "hip-hop" in lower_genre:
            return "Hip-Hop/Rap"
        elif "cantautorato" in lower_genre or lower_genre == "folk":
            return "Folk"
        elif "rock" in lower_genre: 
            return "Rock"
        elif "metal" in lower_genre:
            return "Metal"
        elif "jazz" in lower_genre:
            return "Jazz"
        elif "latin" in lower_genre or lower_genre == "reggaeton":
            return "Latin"
        elif "dance" in lower_genre or "electronic" in lower_genre:
            return "Dance"
        else:
            return "Other"