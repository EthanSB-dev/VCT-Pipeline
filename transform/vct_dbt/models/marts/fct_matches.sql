-- Marts model: the core fact table, one row per match, at match grain.
-- Joins in team names/ids for both sides and the tournament context,
-- ready for BI tools or dashboards.

with staged as (

    select * from {{ ref('stg_matches') }}

),

match_teams as (

    select * from {{ ref('int_match_teams') }}

),

-- Pivot the two per-match team rows into team_a / team_b columns using
-- row_number so we get exactly one row per match regardless of the
-- original opponents array ordering.
ranked_teams as (

    select
        match_id,
        team_id,
        team_name,
        team_acronym,
        score,
        is_winner,
        row_number() over (partition by match_id order by team_id) as team_rank
    from match_teams

),

team_a as (
    select * from ranked_teams where team_rank = 1
),

team_b as (
    select * from ranked_teams where team_rank = 2
),

final as (

    select
        s.match_id,
        s.match_name,
        s.match_status,
        s.match_type,
        s.number_of_games,
        s.is_forfeit,
        s.begin_at,
        s.end_at,
        extract(epoch from (s.end_at - s.begin_at)) / 60.0  as duration_minutes,

        s.tournament_id,
        s.serie_id,
        s.league_id,
        s.league_name,
        s.videogame_version,

        team_a.team_id     as team_a_id,
        team_a.team_name   as team_a_name,
        team_a.score       as team_a_score,

        team_b.team_id     as team_b_id,
        team_b.team_name   as team_b_name,
        team_b.score       as team_b_score,

        s.winner_id,
        s.winner_name

    from staged s
    left join team_a on s.match_id = team_a.match_id
    left join team_b on s.match_id = team_b.match_id

)

select * from final