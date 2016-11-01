from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from residue.models import ResiduePositionSet, ResidueGenericNumberEquivalent
from interaction.models import ResidueFragmentInteraction

import logging

class Command(BaseCommand):
    help = 'Reads source data and creates common database tables'

    logger = logging.getLogger(__name__)

    def purge_residue_sets_(self):
        try:
            ResiduePositionSet.objects.all().delete()
        except Exception as msg:
            print(msg)
            self.logger.warning('Existing data cannot be deleted')

    def handle(self, *args, **options):
        functions = [
            'create_residue_sets',
        ]

        try:
            self.purge_residue_sets_()
            
        except Exception as msg:
            print(msg)
            self.logger.error(msg)

        # execute functions
        for f in functions:
            try:
                getattr(self, f)()
            except Exception as msg:
                print(msg)
                self.logger.error(msg)


    def create_residue_sets(self):
        self.logger.info('CREATING RESIDUE SETS')

        residue_sets = {
            'Signalling protein pocket': ['gpcrdba', ['3x50', '3x53', '3x54', '3x55', '34x50', '34x51', '34x53', '34x54', '5x64', '5x67', '5x68', '5x71', '5x74','6x29', '6x36', '7x55', '8x48', '8x49']],
            'Gprotein Barcode': ['cgn', ['G.hns1.02','G.hns1.03','G.S1.02','G.S3.01','G.S3.03','G.H4.26','G.H4.27','G.h4s6.03','G.h4s6.20','G.H5.11','G.H5.12','G.H5.13','G.H5.15','G.H5.16','G.H5.17','G.H5.19','G.H5.20','G.H5.23','G.H5.24','G.H5.25','G.H5.26']],
            'YM binding site': ['cgn', ['G.H1.02','G.H1.05','G.H1.06','G.H1.09','G.h1ha.01','G.h1ha.04','H.HA.03','H.HA.06','H.HA.07','H.HA.10','G.hfs2.03','G.hfs2.05','G.hfs2.06','G.S2.01','G.S2.02','G.S2.03','G.S2.04']]
                        }
        for set_name in residue_sets.keys():
            residues = []
            for res in residue_sets[set_name][1]:
                try:
                    residues.append(ResidueGenericNumberEquivalent.objects.get(label=res, scheme__slug=residue_sets[set_name][0]))
                except Exception as e: 
                    print(e)
            if residues:
                try:
                    rs = ResiduePositionSet.objects.create(name=set_name)
                    for res in residues:
                        rs.residue_position.add(res)
                except Exception as msg:
                    self.logger.debug('Failed to create residue set {}. Error: {}'.format(set_name, msg))
            self.logger.info('SET {} CREATED'.format(set_name))

        gpcr_class = {
            'gpcrdba':'001',
            #'gpcrdbb': '002',
            'gpcrdbc': '004',
            'gpcrdbf': '005',
            }
        set_names = {
            'gpcrdba': "Class A binding pocket",
#            'gpcrdbb': "Class B binding pocket",
            'gpcrdbc': "Class C binding pocket",
            'gpcrdbf': "Class F binding pocket",
            }
        for c in gpcr_class:
            class_interactions = ResidueFragmentInteraction.objects.filter(
                structure_ligand_pair__structure__protein_conformation__protein__family__slug__startswith=gpcr_class[c], structure_ligand_pair__annotated=True).prefetch_related(
                'rotamer__residue__display_generic_number','interaction_type',
                'structure_ligand_pair__structure__protein_conformation__protein__parent',
                'structure_ligand_pair__ligand__properities')

            generic = {}

            for i in class_interactions:
                if i.rotamer.residue.generic_number:
                    gn = i.rotamer.residue.display_generic_number.label
                else:
                    continue
                if gn not in generic.keys():
                    generic[gn] = 1
                else:
                    generic[gn] += 1
            try:
                rs = ResiduePositionSet.objects.create(name=set_names[c])
            except Exception as msg:
                print(msg)
                self.logger.debug('Failed to create residue set {}. Error: {}'.format(set_names[c], msg))
                continue
            for g in sorted(generic):
                if generic[g] >= 2:
                    bw, gpcrdb = g.split('x')
                    h, pos = bw.split('.')
                    try:
                        rs.residue_position.add(ResidueGenericNumberEquivalent.objects.get(label='{}x{}'.format(h,gpcrdb), scheme__slug=c))
                    except Exception as msg:
                        print(g)
                        print(msg)
                        continue
            self.logger.info('SET {} CREATED'.format(set_names[c]))
        self.logger.info('COMPLETED CREATING RESIDUE SETS')
