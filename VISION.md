# 🎯 Tabitabe Vision & Strategy

> **Last Updated**: 2025-12-06  
> **Status**: Strategic Direction Document

---

## 🌟 Core Vision

**"Pokemon GO for Food" - Turn dining into an epic adventure**

Tabitabe transforms restaurant discovery from a transactional experience into a gamified journey where:
- Every meal is a quest with XP rewards
- Every kilometer traveled earns bonus points  
- Every badge unlocked is a trophy of exploration
- Every local restaurant becomes a hidden dungeon to conquer

---

## 🆚 Competitive Positioning

### Tabitabe vs Tabelog (食べログ)

| Dimension | Tabelog | Tabitabe |
|-----------|---------|----------|
| **Core Value** | Find restaurants → Eat → Done | Continuous adventure loop |
| **Target Audience** | Everyone | Food adventurers (18-45, GenZ/Millennials) |
| **Restaurant Focus** | All types (chains included) | Local & family-owned ONLY |
| **Engagement Model** | One-time transaction | Gamification addiction (levels, badges) |
| **Language** | Japanese only | Japanese + English (AI-translated) |
| **Government** | No relationship | Direct B2G partnerships |
| **Social** | Individual reviews | Community, followers, journeys |
| **Revenue Model** | Ads, premium listings | B2G contracts + Freemium + Gift cards |

### Why We Will Win

1. **Government Moat**: B2G contracts = instant credibility + funding → restaurants trust us
2. **Local Focus**: No competition with big chains → support local = feel-good factor
3. **Gamification Lock-in**: Addiction loop (check-in → earn XP → level up → unlock badges) = retention
4. **Distance Rewards**: Drive 100km? Earn 2000 XP → encourages regional tourism
5. **Community**: Social features create network effect (friends compete on leaderboards)

---

## 🎮 Core Mechanics (The Gamification Loop)

### 1. Experience Points (XP) System

```
Actions that earn XP:
├─ Check-in at restaurant: 50 XP
├─ First-time visit (new restaurant): 100 XP
├─ Write review with photo: 100 XP
├─ Distance bonus: 10-20 XP per km from home
├─ Hidden gem bonus (< 10 reviews): 200 XP
├─ Early bird (before 11am): 50 XP
├─ Regional explorer (3+ prefectures in month): 500 XP
└─ Legendary quest completion: 1000 XP

Level progression:
- Level 1-10: 1000 XP per level
- Level 11-30: 2000 XP per level
- Level 31-50: 5000 XP per level
- Level 51+: 10,000 XP per level
```

### 2. Badge Collection (50+ badges)

**Cuisine Mastery:**
- 🍜 Ramen Master: Visit 10 ramen shops
- 🍣 Sushi Connoisseur: Visit 20 sushi restaurants
- 🍺 Izakaya Regular: Visit 15 izakayas
- 🍛 Curry Hunter: Try 10 different curry shops

**Distance & Travel:**
- 🚗 Road Tripper: Travel 500km total
- 🗾 Prefecture Hopper: Visit 5 different prefectures
- 🏔️ Mountain Climber: Visit restaurant >1000m elevation
- 🌸 All 47 Prefectures (LEGENDARY): Visit all prefectures

**Social & Community:**
- 📸 Photo King: Upload 50 food photos
- ✍️ Review Hero: Write 100 reviews
- 👥 Squad Leader: Create 5 collaborative lists
- 💬 Commenter: Leave 200 helpful comments

**Support Local:**
- 🏠 Local Hero: Visit 30 family-run restaurants
- 💎 Hidden Gem Finder: Discover 10 restaurants with <5 reviews
- 🌟 Early Supporter: Be first reviewer at 5 restaurants
- 🎁 Gift Giver: Purchase ¥10K in gift cards

### 3. Leaderboards (Competitive Engagement)

**Global Leaderboard:**
- Top 100 foodies in all of Japan
- Updated real-time
- Rewards: ¥10K gift card for #1 monthly

**Regional Leaderboards:**
- Top 50 per prefecture
- Top 20 per city
- Local pride + regional competition

**Friends Leaderboard:**
- See how you rank among friends
- Motivates friendly competition

**Restaurant Leaderboards:**
- Most visited restaurant (monthly)
- Highest rated new restaurant
- Hidden gem of the month

### 4. Distance-Based Rewards Formula

```python
def calculate_distance_bonus(distance_km):
    """
    Reward exploration - the further you travel, the more you earn
    """
    if distance_km < 5:
        return 0  # Too close, no bonus
    elif distance_km < 20:
        return int(distance_km * 5)   # 5 XP/km
    elif distance_km < 50:
        return int(distance_km * 10)  # 10 XP/km
    elif distance_km < 100:
        return int(distance_km * 15)  # 15 XP/km
    else:
        return int(distance_km * 20)  # 20 XP/km

# Example: Drive 80km to remote village restaurant
# Bonus XP: 80 * 15 = 1,200 XP (more than 1 level up!)
```

---

## 💰 Revenue Model (3-Stream Strategy)

### Stream 1: B2G (Government Partnerships) - 40% Revenue

**Target**: Prefecture/City governments wanting tourism stimulus

**Value Proposition:**
"Replace paper vouchers with digital, trackable, fraud-proof campaigns"

**Pricing:**
- Setup fee: ¥500,000 (one-time per region)
- Monthly platform fee: ¥100,000
- Gift card commission: 5-10% of campaign budget

**Example Deal:**
```
Kanazawa City signs 1-year contract:
├─ Setup: ¥500,000
├─ Platform fee: ¥100,000 × 12 = ¥1,200,000
├─ Campaign: ¥10M budget → ¥500,000 commission (5%)
└─ Total Year 1: ¥2,200,000 from 1 city

Target: 10 cities Year 1 = ¥22M
```

### Stream 2: B2B (Restaurant Freemium) - 30% Revenue

**Free Tier:**
- Basic listing
- Up to 20 menu items
- AI-translated menu (90% accuracy)
- Self-service profile management

**Premium Tier** (¥5,000/month):
- Featured placement in search
- Professional human translation
- Unlimited menu items
- Advanced analytics dashboard
- Campaign creation tools
- Priority support

**Target:**
- Year 1: 500 restaurants, 40% premium adoption = 200 × ¥5K × 12 = ¥12M

### Stream 3: B2C (Customer Freemium) - 20% Revenue

**Free Tier:**
- Full features (check-in, reviews, badges)
- Shows ads (non-intrusive)
- 5 saved searches

**Premium** (¥500/month):
- Ad-free experience
- Exclusive badges (Premium-only)
- 2x XP multiplier
- 50 saved searches
- Priority customer support

**Premium Plus** (¥1,000/month):
- All Premium features
- 3x XP multiplier
- Unlimited saved searches
- Early access to new features
- Custom profile themes

**Target:**
- Year 1: 50,000 users, 2% premium = 1,000 × ¥500 × 12 = ¥6M

### Stream 4: Advertiser Platform (Phase 3) - 10% Revenue

- Local businesses sponsor badges/challenges
- Example: "Visit 5 restaurants serving Asahi beer → unlock Asahi badge"
- Pricing: ¥50K-200K/month per campaign

---

## 🚀 Go-to-Market Strategy

### Phase 1: Government Pilot (Month 1-3)

**Target**: 1 declining rural prefecture (Shimane or Tottori)

**Why rural?**
- ✅ Government EAGER for tourism solutions
- ✅ Less competition (Tabelog weak in rural areas)
- ✅ Easier to show measurable impact (small baseline)
- ✅ Prove concept before scaling

**Execution:**
1. Approach prefecture tourism board with proposal
2. Offer FREE 3-month pilot (no cost to government)
3. Onboard 30-50 local restaurants (all free tier)
4. Run small campaign (¥5M government budget)
5. Measure results: tourist visits, economic impact
6. Get testimonial + case study

**Success Metrics:**
- 30% increase in tourist restaurant visits
- ¥5M campaign → ¥25M economic activity (5x ROI)
- 80%+ restaurant satisfaction
- Government agrees to paid contract

### Phase 2: Regional PMF (Month 4-6)

**Target**: Kanazawa (金沢) - tourist hotspot, NOT Tokyo

**Why Kanazawa?**
- ✅ Popular tourist destination (2M visitors/year)
- ✅ Famous for local cuisine (seafood, traditional dishes)
- ✅ City government proactive about tourism
- ✅ Not oversaturated like Tokyo/Kyoto
- ✅ English-speaking tourists need help

**Execution:**
1. Sign paid contract with Kanazawa city (¥2.2M/year)
2. Onboard 100 quality local restaurants
3. Heavy marketing: Instagram, TikTok, tourism websites
4. Partner with hotels/ryokans for promotion
5. Run government gift card campaign (¥20M)

**Success Metrics:**
- 5,000 active users
- 100 restaurants enrolled (80% satisfaction)
- 10,000 check-ins/month
- ¥20M campaign fully redeemed
- 4.5+ star app rating

### Phase 3: Multi-Region Scale (Month 7-12)

**Target**: 5 tourist-heavy prefectures

1. **Kyoto (京都)**: Cultural tourism, international visitors
2. **Hiroshima (広島)**: Peace tourism + seafood
3. **Nagano (長野)**: Ski resorts + local soba
4. **Fukuoka (福岡)**: Ramen capital, gateway to Asia
5. **Hokkaido (北海道)**: Sapporo + Niseko ski resorts

**Execution:**
- Replicate Kanazawa playbook per region
- Each region: 100+ restaurants
- Use case studies from Phase 1 & 2
- Hire 1 regional admin per area

**Success Metrics:**
- 50,000 MAU
- 500 restaurants enrolled
- 50,000 check-ins/month
- ¥100M in government campaigns
- ¥46M annual revenue

### Phase 4: National Expansion (Year 2)

- All 47 prefectures
- 5,000+ restaurants
- 500,000+ users
- International expansion prep (Korea, Taiwan)

---

## 🛡️ Competitive Moats (Why We Win Long-Term)

### 1. Government Relationship Moat

- Once signed, governments don't want to switch platforms (data lock-in)
- Multi-year contracts create stable recurring revenue
- Government endorsement = trust signal to restaurants & users
- Competitors can't easily replicate B2G relationships

### 2. Gamification Network Effect

- More users → more competition on leaderboards → more engagement
- Badge collection = sunk cost fallacy (invested time, don't want to switch)
- Social features (followers, squads) = switching cost
- Level 87 user won't switch to competitor and start at Level 1

### 3. Local Restaurant Exclusive Focus

- Big chains (McDonald's, Yoshinoya) not allowed
- Creates unique identity: "Support local businesses"
- Restaurants feel valued (not competing with chains)
- Differentiation from Tabelog (which accepts everyone)

### 4. Data Moat (Long-Term)

- Distance traveled data = unique insights (Strava has this in fitness)
- Gamification behavior data = predict churn, optimize rewards
- Government campaign effectiveness data = sell analytics back to government
- Restaurant performance data = predictive success scoring

---

## 📊 Success Metrics (KPIs)

### Customer Engagement

| Metric | Target (Month 6) | Target (Year 1) |
|--------|------------------|-----------------|
| Monthly Active Users (MAU) | 5,000 | 50,000 |
| Daily Active Users (DAU) | 1,500 | 15,000 |
| DAU/MAU Ratio | 30% | 30% |
| Avg check-ins per user/month | 4 | 5 |
| D7 Retention | 40% | 45% |
| D30 Retention | 25% | 30% |
| Avg session time | 8 min | 10 min |
| Reviews per active user | 1.5 | 2.0 |

### Business Health

| Metric | Target (Month 6) | Target (Year 1) |
|--------|------------------|-----------------|
| MRR (Monthly Recurring Revenue) | ¥1.5M | ¥3.8M |
| Annual Run Rate | ¥18M | ¥46M |
| Customer Acquisition Cost (CAC) | ¥800 | ¥500 |
| Lifetime Value (LTV) | ¥4,000 | ¥5,000 |
| LTV:CAC Ratio | 5:1 | 10:1 |
| Gross Margin | 65% | 70% |
| Monthly Burn Rate | ¥2M | ¥3M |
| Months to Profitability | 12 | Break-even Month 14 |

### Restaurant Success

| Metric | Target (Month 6) | Target (Year 1) |
|--------|------------------|-----------------|
| Total Restaurants | 100 | 500 |
| Premium Restaurants | 30 (30%) | 200 (40%) |
| Avg reviews per restaurant | 5 | 15 |
| Restaurant satisfaction | 80% | 85% |
| Churn rate (monthly) | 5% | 3% |

---

## ⚠️ Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Tabelog copies gamification** | Medium | High | Move fast, government moat, community |
| **Low restaurant adoption** | High | High | Government backing = credibility |
| **GPS fraud (fake check-ins)** | Medium | Medium | Multi-layer verification (QR, receipt, velocity) |
| **User fatigue (burnout)** | Medium | Medium | Vary rewards, seasonal events, social features |
| **Government bureaucracy** | High | Medium | Start with eager rural prefectures |
| **English translation quality** | Low | Medium | AI + human review, restaurant can edit |
| **Chicken-egg problem** | High | High | Government campaign = instant users + budget |
| **Scalability issues** | Low | High | Monolith → replicas → microservices (if needed) |

---

## 🎯 Next Steps (Implementation Priority)

### Immediate (This Month):
1. ✅ **RBAC Refactoring** - Implement Role/Permission/UserRole models
2. ✅ **Government User Type** - Add government official role
3. ✅ **Gamification Models** - Badge, Level, CheckIn, ExperienceLog
4. ✅ **Distance Calculation** - Haversine formula + anti-fraud

### Month 2:
1. □ **Customer APIs** - Check-in, reviews, profile
2. □ **Gamification APIs** - XP earning, badge unlocking, leaderboards
3. □ **Government APIs** - Campaign creation, analytics dashboard
4. □ **English Translation** - OpenAI GPT-4 integration

### Month 3:
1. □ **Mobile PWA** - Customer app (Next.js)
2. □ **Restaurant Portal** - Tablet PWA (Next.js)
3. □ **Government Portal** - Desktop dashboard
4. □ **Pilot Launch** - Shimane or Tottori prefecture

---

**Document Owner**: CEO (You)  
**Last Review**: 2025-12-06  
**Next Review**: 2025-12-20
