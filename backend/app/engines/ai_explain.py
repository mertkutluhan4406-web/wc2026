def generate_ai_explanation(comparison_result: dict, player_a: dict, player_b: dict) -> dict:
    mode = comparison_result["mode"]
    name_a = comparison_result["player_a_name"]
    name_b = comparison_result["player_b_name"]
    
    score_a = comparison_result["overall_a"]
    score_b = comparison_result["overall_b"]
    
    season_a = comparison_result["player_a_season"]
    season_b = comparison_result["player_b_season"]
    
    # Resolve actual years for descriptions
    year_a = player_a["career_peak_season"] if season_a == "Peak" else season_a
    year_b = player_b["career_peak_season"] if season_b == "Peak" else season_b
    
    # Retrieve resolved stats info
    stats_a = player_a["seasons"].get(year_a, player_a["seasons"]["2025-26"])
    stats_b = player_b["seasons"].get(year_b, player_b["seasons"]["2025-26"])
    
    league_a = stats_a["league"]
    league_b = stats_b["league"]
    
    wc_fit_a = comparison_result["wc_fit_a"]["overall_fit_score"]
    wc_fit_b = comparison_result["wc_fit_b"]["overall_fit_score"]
    
    clutch_a = comparison_result["clutch_a"]
    clutch_b = comparison_result["clutch_b"]
    
    dep_a = comparison_result["system_dependency_a"]
    dep_b = comparison_result["system_dependency_b"]
    
    # 1. Season & Peak Custom Intro
    intro_parts = []
    if season_a == "Peak":
        intro_parts.append(f"**{name_a}** oyuncusunun kariyer zirvesi olan **{year_a}** prime dönemi")
    else:
        intro_parts.append(f"**{name_a}** oyuncusunun **{season_a}** sezonundaki performansı")
        
    if season_b == "Peak":
        intro_parts.append(f"**{name_b}** oyuncusunun kariyer zirvesi olan **{year_b}** prime dönemi")
    else:
        intro_parts.append(f"**{name_b}** oyuncusunun **{season_b}** sezonundaki performansı")
        
    summary = f"Bu analizde, {intro_parts[0]} ile {intro_parts[1]} karşılaştırılmıştır. Analiz odağı **{mode}** modu olarak seçilmiştir."
    
    insights = []
    
    # 2. Season specific historical analysis comments
    if season_a == "Peak" or season_b == "Peak":
        insights.append(
            f"**Zirve Sezon (Peak) Analizi:** Kıyaslama, oyuncuların kendilerini en çok ispatladığı altın yılları baz almaktadır. "
            f"{name_a if season_a == 'Peak' else name_b} zirve döneminde taşıyıcı rol üstlenmiştir."
        )
    
    # 3. League Normalization Insight
    if league_a != league_b:
        coef_a = 1.00 if league_a == "Premier League" else 0.93 if league_a == "La Liga" else 0.90
        coef_b = 1.00 if league_b == "Premier League" else 0.93 if league_b == "La Liga" else 0.90
        
        stronger_league = league_a if coef_a > coef_b else league_b
        weaker_league = league_b if coef_a > coef_b else league_a
        adv_player = name_a if coef_a < coef_b else name_b
        
        insights.append(
            f"**Sezonsal Lig Normalizasyonu:** Oyuncuların ilgili sezonda oynadığı lig katsayıları adapte edilmiştir. "
            f"{weaker_league} liginde mücadele eden {adv_player} oyuncusunun ham istatistikleri, {stronger_league} zorluk derecesine göre dengelenmiştir."
        )
    else:
        insights.append(
            f"Kıyaslanan sezonlarda her iki oyuncu da aynı ligde ({league_a}) oynadığı için doğrudan istatistiksel kıyas yapılmıştır."
        )
        
    # 4. Mode Specific Analysis
    if mode == "Offensive":
        goals_a = stats_a["raw_stats"].get("goals", 0)
        goals_b = stats_b["raw_stats"].get("goals", 0)
        xg_a = stats_a["raw_stats"].get("xG", 0)
        xg_b = stats_b["raw_stats"].get("xG", 0)
        
        eff_a = goals_a - xg_a
        eff_b = goals_b - xg_b
        
        if eff_a > 0:
            insights.append(f"**{name_a}**, seçilen sezonda xG beklentisinin üzerine çıkarak bitiricilikte ekstra katkı sağladı (+{round(eff_a, 1)} verim).")
        if eff_b > 0:
            insights.append(f"**{name_b}**, seçilen sezonda xG beklentisinin üzerine çıkarak bitiricilikte ekstra katkı sağladı (+{round(eff_b, 1)} verim).")
            
        if goals_a > goals_b:
            insights.append(f"Gol sayılarında **{name_a}** daha üretkendir ({goals_a} gol vs {goals_b} gol).")
        else:
            insights.append(f"Gol sayılarında **{name_b}** daha üretkendir ({goals_b} gol vs {goals_a} gol).")
            
    elif mode == "Defensive":
        tackles_a = stats_a["defensive_stats"].get("tackles", 0)
        tackles_b = stats_b["defensive_stats"].get("tackles", 0)
        recoveries_a = stats_a["defensive_stats"].get("recoveries", 0)
        recoveries_b = stats_b["defensive_stats"].get("recoveries", 0)
        
        if tackles_a > tackles_b:
            insights.append(f"Savunma kesiciliğinde **{name_a}** ({tackles_a} müdahale) daha etkindir.")
        else:
            insights.append(f"Savunma kesiciliğinde **{name_b}** ({tackles_b} müdahale) daha etkindir.")
            
        if recoveries_a > recoveries_b:
            insights.append(f"Sahipsiz top kazanma (recovery) istatistiğinde **{name_a}** ({recoveries_a}) rakibine üstünlük kurmuştur.")
        else:
            insights.append(f"Sahipsiz top kazanma (recovery) istatistiğinde **{name_b}** ({recoveries_b}) rakibine üstünlük kurmuştur.")
            
    elif mode == "Creativity" or mode == "Passing":
        key_passes_a = stats_a["raw_stats"].get("key_passes", 0)
        key_passes_b = stats_b["raw_stats"].get("key_passes", 0)
        xa_a = stats_a["raw_stats"].get("xA", 0)
        xa_b = stats_b["raw_stats"].get("xA", 0)
        
        if key_passes_a > key_passes_b:
            insights.append(f"**{name_a}**, kilit pas ({key_passes_a}) üretimiyle oyun kurucu rolünü üstlenmiştir.")
        else:
            insights.append(f"**{name_b}**, kilit pas ({key_passes_b}) üretimiyle oyun kurucu rolünü üstlenmiştir.")
            
        insights.append(f"Beklenen asist (xA) kalitesinde liderlik: **{name_a if xa_a > xa_b else name_b}** ({max(xa_a, xa_b)} xA).")
        
    elif mode == "World Cup Impact" or mode == "Overall":
        if wc_fit_a > wc_fit_b:
            insights.append(f"**Dünya Kupası Uyum Analizi:** {name_a} ({wc_fit_a}), turnuva formatına {name_b} ({wc_fit_b}) oyuncusuna kıyasla daha uyumludur. Büyük turnuva baskı toleransı bunu desteklemektedir.")
        else:
            insights.append(f"**Dünya Kupası Uyum Analizi:** {name_b} ({wc_fit_b}), turnuva formatına {name_a} ({wc_fit_a}) oyuncusuna kıyasla daha uyumludur. Fiziksel yoğunluk ve baskı altında karar verme metrikleri bunu desteklemektedir.")
            
        if clutch_a > clutch_b:
            insights.append(f"**Clutch (Kritik Anlar) İndeksi:** {name_a} kritik anlarda ve şampiyonluk yolundaki maçlarda ({clutch_a}/100) daha yüksek sorumluluk almıştır.")
        else:
            insights.append(f"**Clutch (Kritik Anlar) İndeksi:** {name_b} kritik anlarda ve şampiyonluk yolundaki maçlarda ({clutch_b}/100) daha yüksek sorumluluk almıştır.")

    # 5. System Dependency Insight
    if dep_a > dep_b:
        insights.append(f"**Sistem Bağımlılığı:** {name_a} ({dep_a}%) taktik sisteme ve takım arkadaşı desteğine daha çok ihtiyaç duyarken, {name_b} ({dep_b}%) bireysel aksiyonlarla skora gidebilmektedir.")
    else:
        insights.append(f"**Sistem Bağımlılığı:** {name_b} ({dep_b}%) taktik sisteme ve takım arkadaşı desteğine daha çok ihtiyaç duyarken, {name_a} ({dep_a}%) bireysel aksiyonlarla skora gidebilmektedir.")

    # 6. Final Verdict
    if score_a > score_b:
        verdict = f"Genel analize göre **{name_a}**, bu karşılaştırma modunda daha avantajlı profile sahiptir (Genel Performans Skoru: {score_a} vs {score_b})."
    elif score_b > score_a:
        verdict = f"Genel analize göre **{name_b}**, bu karşılaştırma modunda daha avantajlı profile sahiptir (Genel Performans Skoru: {score_b} vs {score_a})."
    else:
        verdict = f"Her iki oyuncu da bu kıyaslama modunda dengeli performans değerlerine sahiptir."

    return {
        "summary": summary,
        "insights": insights,
        "verdict": verdict
    }
