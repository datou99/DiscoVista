#!/usr/bin/env python

import sys
import re
import dendropy

class generateNewQuartFreq(object):

    def __init__(self,nameFile,anotFile, freqStatFile, outFile, treeFile):
        self.nameFile = nameFile
        self.anotFile = anotFile
        self.freqStatFile = freqStatFile
        self.outFile = outFile
        self.treeFile = treeFile
        self.g = open(self.outFile,'w')
        self.tree = dendropy.Tree.get(path=self.treeFile, schema="newick", rooting="force-rooted",preserve_underscores=True)

        self.tree.encode_bipartitions()
        self.setEdgesMap()
        self.generate_clades_dict()

        self.map_clades_to_edges()

    def setEdgesMap(self):
        edgeMap = dict()
        allTaxa = {nd.taxon.label for nd in self.tree.leaf_nodes()}
        self.availableNodes = set()
        for nd in self.tree.postorder_node_iter():
            if nd.label is not None and not nd.is_leaf():
                self.availableNodes.add(nd.label)
            edge = nd.edge
            taxaSet = {t.label for t in edge.bipartition.leafset_taxa(self.tree.taxon_namespace)}
            side1Str = ",".join(sorted(list(taxaSet)))
            side2Str = ",".join(sorted(list(allTaxa - taxaSet)))
            edgeMap[side1Str] = edge.length
            edgeMap[side2Str] = edge.length
        self.edgeMap = edgeMap


    def getClades(self, bipartquad1):
        topology = list()
        for quad in bipartquad1:
            quadSet = set(quad.split(", "))
            h = list()

            while quadSet:
                y = list(quadSet)[0]
                if set(self.clades[self.taxaDict[y]]).issubset(quadSet):
                    quadSet = quadSet.difference(set(self.clades[self.taxaDict[y]]))
                    h.append(self.taxaDict[y])
		else:
		    sys.exit("Couldn't map bipartition to clades defined in annotation file. please check your annotation file!")

            topology.append(h)
        return topology

    def getFormattedBipart(self, topology):
        quad0 = ",".join(sorted(topology[0]))
        quad0 = str(int(self.edgeMap[quad0]))
        quad1 = ",".join(sorted(topology[1]))
        quad1 = str(int(self.edgeMap[quad1]))
        if quad0<quad1:
            return quad0 + "," + quad1
        else:
            return quad1 + "," + quad0

    def getKeyFromListClades(self,topology1,topology2):
        formatedTop1 = self.getFormattedBipart(topology1)
        formatedTop2 = self.getFormattedBipart(topology2)
        if formatedTop1 < formatedTop2:
            formatedClade = formatedTop1 + " | " + formatedTop2
        else:
            formatedClade = formatedTop2 + " | " + formatedTop1
        return formatedClade

    def map_taxa_to_clades(self, line):
        flag = True
        key = ""
        lineList = line.strip().strip("\n").split('\t')
        if lineList[0] not in self.availableNodes:
            flag = False
            return (key,flag)
        bipartitions = lineList[2].split("#")
        bipartquad1 = bipartitions[0].replace("}","").replace('|',"").split('{')[1:3]
        bipartquad2 = bipartitions[1].replace("}","").replace('|',"").split('{')[1:3]
        topology1 = self.getClades(bipartquad1)
        topology2 = self.getClades(bipartquad2)
        key = self.getKeyFromListClades(topology1,topology2)
        return (key,flag)

    def generate_clades_dict(self):
        taxaDict = dict()
        allClades = dict()
        for x in open(anotFile).readlines():
            taxaDict[x.split('\t')[0].strip()] = x.split('\t')[1].strip()
            if x.split('\t')[1].strip() not in allClades:
                allClades[x.split('\t')[1].strip()] = list()
                allClades[x.split('\t')[1].strip()].append(x.split('\t')[0].strip())
            else:
                allClades[x.split('\t')[1].strip()].append(x.split('\t')[0].strip())
        self.taxaDict = taxaDict
        self.clades = allClades
        return

    def map_clades_to_edges(self):
        tree = self.tree
        cladeToEdge = dict()
        tree.encode_bipartitions()
        allTaxa = {l.taxon.label.replace("'","") for l in tree.leaf_nodes()}
	flag = 0
        for edge in tree.postorder_internal_edge_iter():
	    #if nd.parent_node == tree.seed_node:
	#	continue
#            edge = nd.edge
            taxa = edge.bipartition.leafset_taxa(tree.taxon_namespace)
            mainTaxaLabels = {l.label.replace("'","") for l in taxa}
            mainotherSide = (allTaxa - mainTaxaLabels)

 #           if nd == tree.seed_node:
  #              continue
	    if edge.head_node == tree.seed_node or edge.tail_node == tree.seed_node:
		children = tree.seed_node.child_nodes()
		if children[0].is_leaf() or children[1].is_leaf() or flag == 1:
			continue
		else:
			neighbors = list()
			e0 = [i for i in children[0].incident_edges() if (i.head_node is not tree.seed_node or i.tail_node is not tree.seed_node)]
			e1 = [i for i in children[1].incident_edges() if (i.head_node is not tree.seed_node or i.tail_node is not tree.seed_node)]
			neighbors = e0 + e1
			flag = 1
	    else:
	            neighbors = edge.get_adjacent_edges()
            if len(neighbors) < 4:
                continue
            h = list()

            bipart1 = list()
            bipart2 = list()
            for e in neighbors:
                taxa = e.bipartition.leafset_taxa(tree.taxon_namespace)
                taxaLabels = sorted([l.label.replace("'","") for l in taxa])
                otherSide = sorted(list(allTaxa - set(taxaLabels)))
                if not taxaLabels or not otherSide:
                    continue
                if set(taxaLabels).issubset(mainTaxaLabels):
                    bipart = ",".join(taxaLabels)
                    bipart1.append(str(int(self.edgeMap[bipart])))
                elif set(taxaLabels).issubset(mainotherSide):
                    bipart = ",".join(taxaLabels)
                    bipart2.append(str(int(self.edgeMap[bipart])))
                elif set(otherSide).issubset(mainTaxaLabels):
                    bipart = ",".join(otherSide)
                    bipart1.append(str(int(self.edgeMap[bipart])))
                elif set(otherSide).issubset(mainotherSide):
                    bipart = ",".join(otherSide)
            	    bipart2.append(str(int(self.edgeMap[bipart])))
	    if len(bipart1)<2:
		continue
            if bipart1[0]<bipart1[1]:
                bipart1String = bipart1[0]+","+bipart1[1]
            else:
                bipart1String = bipart1[1]+","+bipart1[0]
	    if len(bipart2)<2:
		continue
            if bipart2[0]<bipart2[1]:
                bipart2String = bipart2[0]+","+bipart2[1]
            else:
                bipart2String = bipart2[1]+","+bipart2[0]
            if bipart1String < bipart2String:
                bipartString = bipart1String + " | " + bipart2String
            else:
                bipartString = bipart2String + " | " + bipart1String
            edge.label = bipartString
            cladeToEdge[edge.label] = edge
	
        self.cladeToEdge = cladeToEdge


#	def generate_edge_labels():
    def generate_new_freqStat(self):
        self.freqStat = open(self.freqStatFile).readlines()
        Linet = list()
        c = 0
        for i in range(0,len(self.freqStat)):
            line = self.freqStat[i]
            (key, flag) = self.map_taxa_to_clades(line)
            if not flag:
                continue
            if c % 3 == 0:

                Node = str(int(self.cladeToEdge[key].length))
                if c > 0:

                    print >> self.g, "\t".join(Linet[0]) + "\t" + "t1"
                    if Linet[1][2] < Linet[2][2]:
                        print >> self.g,  "\t".join(Linet[1])  + "\t" + "t2"
                        print >> self.g,  "\t".join(Linet[2])  + "\t" + "t3"
                    else:
                        print >> self.g, "\t".join(Linet[2]) + "\t" + "t2"
                        print >> self.g, "\t".join(Linet[1]) + "\t" + "t3"
                Linet = list()
            Linet.append([line.strip("\n"), Node, key])
            c += 1
        print >> self.g, "\t".join(Linet[0]) + "\t" + "t1"
        if Linet[1][2] < Linet[2][2]:
            print >> self.g, "\t".join(Linet[1]) + "\t" + "t2"
            print >> self.g, "\t".join(Linet[2]) + "\t" + "t3"
        else:
            print >> self.g, "\t".join(Linet[2]) + "\t" + "t2"
            print >> self.g, "\t".join(Linet[1]) + "\t" + "t3"
if __name__ == "__main__":
    if (len(sys.argv)<6):
        print "USAGE: " + sys.argv[0] + " NameFiles Anotation freqStat Outfile Tree"
        exit(1)
    namesFile = sys.argv[1]
    anotFile = sys.argv[2]
    freqStatFile = sys.argv[3]
    outFile = sys.argv[4]
    treeList = sys.argv[5]
    generateFreq = generateNewQuartFreq(namesFile, anotFile, freqStatFile, outFile, treeList)
    generateFreq.generate_new_freqStat()

