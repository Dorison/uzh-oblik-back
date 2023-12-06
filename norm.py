from db import db, Gender, Norm, Serviceman, ServicemanObligation, Obligation
from typing import List, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy import or_

@dataclass
class ObligationDto:
    item_id : int
    term: int
    count: int

class NormManager:
    def __init__(self, db):
        self.db = db

    def create_norm(self, genders: List[Gender], from_rank, to_rank, name: str, reason: str, from_date: datetime,
                    to_date: datetime):
        norm = Norm(genders=genders, from_rank=from_rank, to_rank=to_rank, name=name, reason=reason,
                    from_date=from_date, to_date=to_date)
        self.db.session.add(norm)
        self.db.session.commit()
        return norm.id

    def add_group(self, norm_id, name, obligations: List[ObligationDto]):
        for obligation in obligations:
            self.db.session.add(Obligation(norm_id=norm_id, group=name, item_id=obligation.item_id, count=obligation.count, term=obligation.term))
        self.db.session.commit()

    def get_groups(self):
        query = self.db.select(Obligation.group).distinct()
        return self.db.session.execute(query).scalars()
    def get_norm(self, norm_id):
        return db.get_or_404(Norm, norm_id)

    def get_all(self):
        query = self.db.select(Norm)
        return db.session.execute(query).scalars()

    def get_potential_norms(self, serviceman: Serviceman):
        gender = serviceman.gender
        ranks = serviceman.get_ranks()
        service_date = serviceman.rank_history[0]
        """
        (db.select(Issue).filter(Issue.expire > from_date).filter(Issue.expire < to_date)
         .order_by(Issue.expire)

            
            filter(Norm.to_date is None or Norm.to_date > service_date)
             
             Norm.to_date == None or 
         """
        query = self.db.select(Norm).filter(Norm.genders.contains([gender]), Norm.from_rank <= ranks[-1], Norm.to_rank >= ranks[0], or_(Norm.to_date == None,Norm.to_date > service_date)).order_by(Norm.from_date)
        return db.session.execute(query).scalars()

    @staticmethod
    def get_obligations(serviceman: Serviceman, norms: List[Norm], end_date: datetime) -> Dict[int, List[ServicemanObligation]]:
        def get_time_interval(norm: Norm):
            start = norm.from_date
            end = end_date if norm.to_date is None else norm.to_date
            if len(serviceman.rank_history) > norm.from_rank:
                applicable_date = serviceman.rank_history[norm.from_rank]
                if applicable_date > end:
                    return None
                start = max(applicable_date, start)
            else:
                return None
            if len(serviceman.rank_history) > norm.to_rank+1:
                deapllicable_date = serviceman.rank_history[norm.to_rank+1]
                if deapllicable_date < start:
                    return None
                end = min(deapllicable_date, end)
            return start, end

        obligations: Dict[int, List[ServicemanObligation]] = {}
        for norm in norms:
            time_interval = get_time_interval(norm)
            if time_interval:
                start, end = time_interval
                for obligation in norm.obligations:
                    item = obligation.item
                    if serviceman.group == obligation.group:
                        if item.returnable:
                            if end == end_date:
                                if item.id not in obligations:
                                    # TODO sizes
                                    obligations[item.id] = [
                                        ServicemanObligation(item, None, obligation.count, datetime.now(),
                                                             obligation.term)]
                        else:
                            time = start
                            if item.id in obligations:
                                time = obligations[item.item.id][-1].date + timedelta(days=obligation.term)
                            while time <= end:
                                # TODO sizes
                                serviceman_obligation = ServicemanObligation(item, None, obligation.count, time,
                                                                             obligation.term)
                                if item.id in obligations:
                                    obligations[item.id].append(serviceman_obligation)
                                else:
                                    obligations[item.id] = [serviceman_obligation]
                                time += timedelta(days=obligation.term)
        for issue in serviceman.issues:
            if issue.item.returnable:
                for serviceman_obligation in obligations[issue.item.id]:
                    if serviceman_obligation.date - issue.date < timedelta(serviceman_obligation.term):
                        serviceman_obligation.count -= issue.count
                        break
                if serviceman_obligation.count == 0:
                    obligations[issue.item.id].remove(serviceman_obligation)
            else:
                for serviceman_obligation in obligations[issue.item.id]:
                    if issue.date == serviceman_obligation.date:
                        serviceman_obligation.count -= issue.count
                        break
                else:
                    raise Exception(f"{issue} not found in {obligations[issue.item.id]}")
                if serviceman_obligation.count == 0:
                    obligations[issue.item.id].remove(serviceman_obligation)
        return obligations


norm_manager = NormManager(db)
